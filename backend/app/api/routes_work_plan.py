from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.db.session import get_db, SessionLocal
from app.services.auth_service import AuthService
from app.services.request_service import RequestService
from app.schemas.request import RequestResponse, RequestUpdate
from app.schemas.work_plan import PlanRequestsRequest
from app.models.request import Request, RequestStatus

router = APIRouter()


def require_tech_or_admin(current_user: dict = Depends(AuthService.get_current_user)):
    """Tech veya Admin yetkisi kontrolü"""
    if current_user["role"] not in ["admin", "tech"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için tech veya admin yetkisi gereklidir"
        )
    return current_user


@router.get("/pending", response_model=List[RequestResponse])
async def get_pending_requests(
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tech_or_admin)
):
    """Bekleyen işleri getir (iş planı için)"""
    request_service = RequestService(db)
    
    # Depot filtresi: Kullanıcının depot_ids'leri varsa onları kullan
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        # Backward compatibility
        user_depot_ids = [current_user["depot_id"]]
    
    # Eğer parametre olarak depot_id verilmişse, sadece o depoyu kullan
    if depot_id:
        # Admin ise tüm depoları görebilir, tech ise sadece kendi depolarını
        if current_user["role"] == "admin" or depot_id in user_depot_ids:
            user_depot_ids = [depot_id]
        else:
            # Tech kullanıcı kendi deposu dışında bir depo seçemez
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu depo için yetkiniz yok"
            )
    
    # Sadece "Beklemede" durumundaki talepleri getir
    query = db.query(Request).filter(Request.status == RequestStatus.BEKLEMEDE.value)
    
    # Tech kullanıcılar sadece kendi depolarındaki işleri görebilir
    if current_user["role"] != "admin" and user_depot_ids:
        query = query.filter(Request.depot_id.in_(user_depot_ids))
    elif depot_id:
        query = query.filter(Request.depot_id == depot_id)
    
    requests = query.order_by(Request.requested_date.asc()).all()
    
    return [request_service._to_response(r, include_user=True) for r in requests]


@router.post("/plan", response_model=dict)
async def plan_requests(
    plan_data: PlanRequestsRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tech_or_admin)
):
    """İşleri planla (planlanan tarih ekle ve durumu güncelle)"""
    request_service = RequestService(db)
    updated_count = 0
    errors = []
    
    request_ids = plan_data.request_ids
    planned_date = plan_data.planned_date
    
    for request_id in request_ids:
        try:
            request = db.query(Request).filter(Request.id == request_id).first()
            if not request:
                errors.append(f"Talep {request_id} bulunamadı")
                continue
            
            # Durum kontrolü - sadece "Beklemede" olanlar planlanabilir
            if request.status != RequestStatus.BEKLEMEDE.value:
                errors.append(f"Talep {request_id} zaten planlanmış veya tamamlanmış")
                continue
            
            # Planlanan tarih ve durum güncelle
            update_data = RequestUpdate(
                status=RequestStatus.TAKVIME_EKLENDI.value,
                planned_date=planned_date
            )
            
            updated_request = request_service.update_request(
                request_id=request_id,
                update_data=update_data,
                updated_by_id=current_user["id"]
            )
            if updated_request:
                updated_count += 1
            
        except Exception as e:
            errors.append(f"Talep {request_id}: {str(e)[:100]}")
            continue
    
    db.commit()
    
    # Bildirim gönder (background task)
    def send_plan_notifications():
        try:
            from app.services.notification_service import NotificationService
            from app.models.user import User
            import asyncio
            
            bg_db = SessionLocal()
            try:
                notification_service = NotificationService(bg_db)
                updated_by_user = bg_db.query(User).filter(User.id == current_user["id"]).first()
                
                if not updated_by_user:
                    return
                
                # Planlanan her talep için bildirim gönder
                for request_id in request_ids:
                    try:
                        request = bg_db.query(Request).filter(Request.id == request_id).first()
                        if request and request.planned_date:
                            # Talep sahibine bildirim gönder
                            request_owner = bg_db.query(User).filter(User.id == request.user_id).first()
                            if request_owner and request_owner.email:
                                asyncio.run(notification_service.notify_request_planned(
                                    request,
                                    request.planned_date.strftime("%d.%m.%Y"),
                                    updated_by_user
                                ))
                    except Exception as e:
                        print(f"⚠️ Talep {request_id} için bildirim hatası: {e}")
            finally:
                bg_db.close()
        except Exception as e:
            print(f"⚠️ Planlama bildirimi hatası: {e}")
            import traceback
            traceback.print_exc()
    
    background_tasks.add_task(send_plan_notifications)
    
    return {
        "success": True,
        "updated": updated_count,
        "errors": errors[:10]
    }


@router.get("/planned", response_model=List[RequestResponse])
async def get_planned_requests(
    depot_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    mine: bool = Query(False),  # Kullanıcının kendi talepleri
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Planlanmış işleri getir (tech/admin tüm depo, user sadece kendi talepleri)"""
    request_service = RequestService(db)
    
    # Kullanıcı sadece kendi taleplerini görebilir
    if mine or current_user["role"] == "user":
        user_requests = request_service.get_user_requests(
            current_user["email"],
            depot_id=current_user.get("depot_id")
        )
        # Sadece planlanmış olanları filtrele
        planned_user_requests = [r for r in user_requests if r.planlananTarih]
        return planned_user_requests
    
    # Tech/Admin için depot filtresi
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        user_depot_ids = [current_user["depot_id"]]
    
    query = db.query(Request).filter(Request.status == RequestStatus.TAKVIME_EKLENDI.value)
    
    # Tech kullanıcılar sadece kendi depolarındaki işleri görebilir
    if current_user["role"] == "tech" and user_depot_ids:
        if depot_id and depot_id not in user_depot_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu depo için yetkiniz yok"
            )
        query = query.filter(Request.depot_id.in_(user_depot_ids))
    elif depot_id:
        query = query.filter(Request.depot_id == depot_id)
    
    if start_date:
        query = query.filter(Request.planned_date >= start_date)
    
    if end_date:
        query = query.filter(Request.planned_date <= end_date)
    
    requests = query.order_by(Request.planned_date.asc()).all()
    
    return [request_service._to_response(r, include_user=True) for r in requests]
