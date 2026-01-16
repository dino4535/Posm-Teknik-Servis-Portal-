from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import date, datetime, timedelta
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.models.request import Request, RequestStatus
from app.models.user import User
from app.models.dealer import Dealer
from app.models.depot import Depot
from app.models.territory import Territory
from app.models.posm import Posm
from app.models.photo import Photo
from pydantic import BaseModel
import pandas as pd
import io

router = APIRouter()


def require_admin(current_user: dict = Depends(AuthService.get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


class ReportStatsResponse(BaseModel):
    total_requests: int
    pending_requests: int
    planned_requests: int
    completed_requests: int
    cancelled_requests: int
    by_depot: dict
    by_job_type: dict
    by_status: dict
    completion_rate: float
    avg_completion_time_days: Optional[float] = None


class DetailedReportItem(BaseModel):
    id: int
    talep_tarihi: str
    durum: str
    oncelik: Optional[str]
    bayi_kodu: str
    bayi_adi: str
    territory: Optional[str]
    depo: Optional[str]
    yapilacak_is: str
    is_detayi: Optional[str]
    posm_adi: Optional[str]
    planlanan_tarih: Optional[str]
    tamamlanma_tarihi: Optional[str]
    olusturan_kullanici: str
    olusturan_email: str
    tamamlayan_kullanici: Optional[str]
    guncelleyen_kullanici: Optional[str]
    fotoğraf_sayisi: int
    enlem: Optional[str]
    boylam: Optional[str]
    tamamlanma_suresi_gun: Optional[int]


@router.get("/stats", response_model=ReportStatsResponse)
async def get_report_stats(
    depot_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Rapor istatistikleri"""
    query = db.query(Request)
    
    # Depot filtresi
    if depot_id:
        query = query.filter(Request.depot_id == depot_id)
    
    # Tarih filtresi
    if start_date:
        query = query.filter(Request.request_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Request.request_date <= datetime.combine(end_date, datetime.max.time()))
    
    all_requests = query.all()
    
    # Genel istatistikler
    total = len(all_requests)
    pending = len([r for r in all_requests if r.status == RequestStatus.BEKLEMEDE.value])
    planned = len([r for r in all_requests if r.status == RequestStatus.TAKVIME_EKLENDI.value])
    completed = len([r for r in all_requests if r.status == RequestStatus.TAMAMLANDI.value])
    cancelled = len([r for r in all_requests if r.status == RequestStatus.IPTAL.value])
    
    # Depo bazında
    by_depot = {}
    depot_query = db.query(Depot).all()
    for depot in depot_query:
        depot_requests = [r for r in all_requests if r.depot_id == depot.id]
        by_depot[depot.name] = {
            "total": len(depot_requests),
            "pending": len([r for r in depot_requests if r.status == RequestStatus.BEKLEMEDE.value]),
            "completed": len([r for r in depot_requests if r.status == RequestStatus.TAMAMLANDI.value])
        }
    
    # İş tipi bazında
    by_job_type = {
        "Montaj": len([r for r in all_requests if r.job_type == "Montaj"]),
        "Demontaj": len([r for r in all_requests if r.job_type == "Demontaj"]),
        "Bakım": len([r for r in all_requests if r.job_type == "Bakım"])
    }
    
    # Durum bazında
    by_status = {
        "Beklemede": pending,
        "TakvimeEklendi": planned,
        "Tamamlandı": completed,
        "İptal": cancelled
    }
    
    # Tamamlanma oranı
    completion_rate = (completed / total * 100) if total > 0 else 0.0
    
    # Ortalama tamamlanma süresi (gün)
    completed_with_dates = [
        r for r in all_requests 
        if r.status == RequestStatus.TAMAMLANDI.value and r.completed_date and r.request_date
    ]
    avg_completion_time = None
    if completed_with_dates:
        total_days = sum([
            (r.completed_date - r.request_date.date()).days 
            for r in completed_with_dates
        ])
        avg_completion_time = total_days / len(completed_with_dates) if len(completed_with_dates) > 0 else None
    
    return ReportStatsResponse(
        total_requests=total,
        pending_requests=pending,
        planned_requests=planned,
        completed_requests=completed,
        cancelled_requests=cancelled,
        by_depot=by_depot,
        by_job_type=by_job_type,
        by_status=by_status,
        completion_rate=round(completion_rate, 2),
        avg_completion_time_days=round(avg_completion_time, 2) if avg_completion_time else None
    )


@router.get("/detailed", response_model=List[DetailedReportItem])
async def get_detailed_report(
    depot_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status_filter: Optional[str] = Query(None),
    job_type_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Detaylı rapor - Tüm talep detayları"""
    query = db.query(Request).join(Dealer).join(User, Request.user_id == User.id)
    
    # Depot filtresi
    if depot_id:
        query = query.filter(Request.depot_id == depot_id)
    
    # Tarih filtresi
    if start_date:
        query = query.filter(Request.request_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Request.request_date <= datetime.combine(end_date, datetime.max.time()))
    
    # Durum filtresi
    if status_filter:
        query = query.filter(Request.status == status_filter)
    
    # İş tipi filtresi
    if job_type_filter:
        query = query.filter(Request.job_type == job_type_filter)
    
    requests = query.order_by(Request.request_date.desc()).all()
    
    result = []
    for req in requests:
        # Territory
        territory_name = None
        if req.territory:
            territory_name = req.territory.name
        
        # Depo
        depot_name = None
        if req.depot:
            depot_name = req.depot.name
        
        # POSM
        posm_name = None
        if req.posm:
            posm_name = req.posm.name
        
        # Tamamlayan kullanıcı
        completed_by_name = None
        if req.completed_by_user:
            completed_by_name = req.completed_by_user.name
        
        # Güncelleyen kullanıcı
        updated_by_name = None
        if req.updated_by_user:
            updated_by_name = req.updated_by_user.name
        
        # Fotoğraf sayısı
        photo_count = db.query(Photo).filter(Photo.request_id == req.id).count()
        
        # Tamamlanma süresi (gün)
        completion_days = None
        if req.completed_date and req.request_date:
            completion_days = (req.completed_date - req.request_date.date()).days
        
        # Koordinatlar
        lat = None
        lng = None
        if req.latitude is not None:
            lat = str(req.latitude)
        elif req.dealer and req.dealer.latitude is not None:
            lat = str(req.dealer.latitude)
        
        if req.longitude is not None:
            lng = str(req.longitude)
        elif req.dealer and req.dealer.longitude is not None:
            lng = str(req.dealer.longitude)
        
        result.append(DetailedReportItem(
            id=req.id,
            talep_tarihi=req.request_date.strftime("%d.%m.%Y %H:%M") if req.request_date else "",
            durum=req.status,
            oncelik=req.priority,
            bayi_kodu=req.dealer.code,
            bayi_adi=req.dealer.name,
            territory=territory_name,
            depo=depot_name,
            yapilacak_is=req.job_type,
            is_detayi=req.job_detail,
            posm_adi=posm_name,
            planlanan_tarih=req.planned_date.strftime("%d.%m.%Y") if req.planned_date else None,
            tamamlanma_tarihi=req.completed_date.strftime("%d.%m.%Y") if req.completed_date else None,
            olusturan_kullanici=req.user.name,
            olusturan_email=req.user.email,
            tamamlayan_kullanici=completed_by_name,
            guncelleyen_kullanici=updated_by_name,
            fotoğraf_sayisi=photo_count,
            enlem=lat,
            boylam=lng,
            tamamlanma_suresi_gun=completion_days
        ))
    
    return result


@router.get("/export/excel")
async def export_to_excel(
    depot_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status_filter: Optional[str] = Query(None),
    job_type_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Excel olarak detaylı rapor export"""
    # Detaylı rapor verilerini al
    query = db.query(Request).join(Dealer).join(User, Request.user_id == User.id)
    
    # Filtreler
    if depot_id:
        query = query.filter(Request.depot_id == depot_id)
    if start_date:
        query = query.filter(Request.request_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Request.request_date <= datetime.combine(end_date, datetime.max.time()))
    if status_filter:
        query = query.filter(Request.status == status_filter)
    if job_type_filter:
        query = query.filter(Request.job_type == job_type_filter)
    
    requests = query.order_by(Request.request_date.desc()).all()
    
    # Excel için veri hazırla
    data = []
    for req in requests:
        territory_name = req.territory.name if req.territory else None
        depot_name = req.depot.name if req.depot else None
        posm_name = req.posm.name if req.posm else None
        completed_by_name = req.completed_by_user.name if req.completed_by_user else None
        updated_by_name = req.updated_by_user.name if req.updated_by_user else None
        photo_count = db.query(Photo).filter(Photo.request_id == req.id).count()
        
        completion_days = None
        if req.completed_date and req.request_date:
            completion_days = (req.completed_date - req.request_date.date()).days
        
        lat = str(req.latitude) if req.latitude is not None else (str(req.dealer.latitude) if req.dealer and req.dealer.latitude is not None else None)
        lng = str(req.longitude) if req.longitude is not None else (str(req.dealer.longitude) if req.dealer and req.dealer.longitude is not None else None)
        
        data.append({
            "Talep ID": req.id,
            "Talep Tarihi": req.request_date.strftime("%d.%m.%Y %H:%M") if req.request_date else "",
            "Durum": req.status,
            "Öncelik": req.priority or "Orta",
            "Bayi Kodu": req.dealer.code,
            "Bayi Adı": req.dealer.name,
            "Territory": territory_name or "",
            "Depo": depot_name or "",
            "Yapılacak İş": req.job_type,
            "İş Detayı": req.job_detail or "",
            "POSM Adı": posm_name or "",
            "Planlanan Tarih": req.planned_date.strftime("%d.%m.%Y") if req.planned_date else "",
            "Tamamlanma Tarihi": req.completed_date.strftime("%d.%m.%Y") if req.completed_date else "",
            "Oluşturan Kullanıcı": req.user.name,
            "Oluşturan Email": req.user.email,
            "Tamamlayan Kullanıcı": completed_by_name or "",
            "Güncelleyen Kullanıcı": updated_by_name or "",
            "Fotoğraf Sayısı": photo_count,
            "Enlem": lat or "",
            "Boylam": lng or "",
            "Tamamlanma Süresi (Gün)": completion_days if completion_days is not None else ""
        })
    
    # DataFrame oluştur
    df = pd.DataFrame(data)
    
    # Excel dosyası oluştur
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Detaylı Rapor')
        
        # Sütun genişliklerini ayarla
        worksheet = writer.sheets['Detaylı Rapor']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    output.seek(0)
    
    # Dosya adı oluştur
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detayli_rapor_{date_str}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
