from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.posm_service import PosmService
from app.schemas.posm import (
    PosmResponse, PosmCreateRequest, PosmUpdateRequest, 
    PosmStockResponse, PosmTransferRequest, PosmTransferResponse
)
from app.models.depot import Depot
from app.models.posm import Posm

router = APIRouter()


@router.post("/sync-all-depots")
async def sync_posm_to_all_depots(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Tüm mevcut POSM'leri tüm depolar için oluştur (stok 0 ile) - Admin only"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    
    # Tüm depoları getir
    depots = db.query(Depot).all()
    if not depots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hiç depo bulunamadı"
        )
    
    # Tüm mevcut POSM isimlerini getir (benzersiz)
    existing_posms = db.query(Posm.name).distinct().all()
    unique_posm_names = [p[0] for p in existing_posms]
    
    if not unique_posm_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hiç POSM bulunamadı"
        )
    
    created_count = 0
    skipped_count = 0
    
    # Her POSM için her depoyu kontrol et
    for posm_name in unique_posm_names:
        for depot in depots:
            # Bu depoda bu POSM var mı kontrol et
            existing = db.query(Posm).filter(
                Posm.name == posm_name,
                Posm.depot_id == depot.id
            ).first()
            
            if not existing:
                # Yeni POSM oluştur (stok 0 ile)
                new_posm = Posm(
                    name=posm_name,
                    depot_id=depot.id,
                    ready_count=0,
                    repair_pending_count=0
                )
                db.add(new_posm)
                created_count += 1
            else:
                skipped_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"POSM senkronizasyonu tamamlandı",
        "created": created_count,
        "skipped": skipped_count,
        "total_posms": len(unique_posm_names),
        "total_depots": len(depots)
    }


@router.get("/", response_model=list[PosmResponse])
async def get_posm_list(
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM listesini getir (depot filtresi ile)"""
    posm_service = PosmService(db)
    
    # Depot filtresi: Kullanıcının depot_ids'leri varsa onları kullan
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        # Backward compatibility
        user_depot_ids = [current_user["depot_id"]]
    
    # Eğer parametre olarak depot_id verilmişse, sadece o depoyu kullan
    if depot_id:
        # Admin ise tüm depoları görebilir, diğerleri sadece kendi depolarını
        if current_user["role"] == "admin" or depot_id in user_depot_ids:
            return posm_service.get_all_posm(depot_id=depot_id)
        else:
            # Kullanıcı kendi deposu dışında bir depo seçemez
            return []
    
    # Admin ise tüm POSM'leri göster, diğerleri sadece kendi depolarındakileri
    if current_user["role"] == "admin":
        return posm_service.get_all_posm(depot_id=None)
    elif user_depot_ids:
        # Kullanıcının tüm depolarındaki POSM'leri getir
        all_posms = []
        for dep_id in user_depot_ids:
            posms = posm_service.get_all_posm(depot_id=dep_id)
            all_posms.extend(posms)
        # Duplicate'leri kaldır (aynı POSM birden fazla depoda olabilir)
        seen = set()
        unique_posms = []
        for posm in all_posms:
            if posm.id not in seen:
                seen.add(posm.id)
                unique_posms.append(posm)
        return unique_posms
    else:
        # Depot bilgisi yoksa tüm POSM'leri göster (backward compatibility)
        return posm_service.get_all_posm(depot_id=None)


@router.get("/{posm_id}", response_model=PosmResponse)
async def get_posm_details(
    posm_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM detaylarını getir"""
    from app.models.posm import Posm
    
    posm_service = PosmService(db)
    posm = posm_service.get_posm_by_id(posm_id)
    
    if not posm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    # Depot bazlı yetki kontrolü (admin hariç)
    if current_user["role"] != "admin":
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        
        # POSM'in depot_id'sini kontrol et
        posm_obj = db.query(Posm).filter(Posm.id == posm_id).first()
        if posm_obj and posm_obj.depot_id and posm_obj.depot_id not in user_depot_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu POSM'e erişim yetkiniz yok"
            )
    
    return posm


@router.get("/{posm_id}/stock", response_model=PosmStockResponse)
async def get_posm_stock(
    posm_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM stok bilgisini getir"""
    from app.models.posm import Posm
    
    posm_service = PosmService(db)
    stock = posm_service.get_posm_stock(posm_id)
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    # Depot bazlı yetki kontrolü (admin hariç)
    if current_user["role"] != "admin":
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        
        # POSM'in depot_id'sini kontrol et
        posm_obj = db.query(Posm).filter(Posm.id == posm_id).first()
        if posm_obj and posm_obj.depot_id and posm_obj.depot_id not in user_depot_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu POSM'in stok bilgisine erişim yetkiniz yok"
            )
    
    return stock


@router.patch("/{posm_id}", response_model=PosmResponse)
async def update_posm(
    posm_id: int,
    update_data: PosmUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM güncelle (admin only - tech sadece görüntüleyebilir)"""
    # Role kontrolü - sadece admin güncelleyebilir
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    
    # Eski değerleri kaydet (audit log için - güncellemeden önce)
    old_posm = db.query(Posm).filter(Posm.id == posm_id).first()
    if not old_posm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    old_values = {
        "name": old_posm.name,
        "depot_id": old_posm.depot_id,
        "ready_count": old_posm.ready_count,
        "repair_pending_count": old_posm.repair_pending_count
    }
    
    posm_service = PosmService(db)
    posm = posm_service.update_posm(posm_id, update_data)
    
    if not posm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    # Yeni değerleri kaydet
    new_values = {}
    if update_data.name:
        new_values["name"] = update_data.name
    if update_data.ready_count is not None:
        new_values["ready_count"] = update_data.ready_count
    if update_data.repair_pending_count is not None:
        new_values["repair_pending_count"] = update_data.repair_pending_count
    
    # Audit log oluştur
    try:
        from app.services.audit_service import AuditService
        from app.utils.ip_helper import get_client_ip
        audit_service = AuditService(db)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        audit_service.create_log(
            user_id=current_user["id"],
            action="UPDATE",
            entity_type="POSM",
            entity_id=posm_id,
            old_values=old_values,
            new_values=new_values if new_values else None,
            description=f"POSM güncellendi: {posm.name}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    return posm


@router.post("/", response_model=PosmResponse)
async def create_posm(
    posm_data: PosmCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Yeni POSM oluştur (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    
    posm_service = PosmService(db)
    try:
        posm = posm_service.create_posm(posm_data)
        
        # Audit log oluştur
        try:
            from app.services.audit_service import AuditService
            from app.utils.ip_helper import get_client_ip
            audit_service = AuditService(db)
            client_ip = get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            audit_service.create_log(
                user_id=current_user["id"],
                action="CREATE",
                entity_type="POSM",
                entity_id=posm.id,
                new_values={"name": posm.name, "depot_id": posm.depot_id, "ready_count": posm.ready_count},
                description=f"Yeni POSM oluşturuldu: {posm.name}",
                ip_address=client_ip,
                user_agent=user_agent
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
        
        return posm
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{posm_id}")
async def delete_posm(
    posm_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM sil (admin only)"""
    from app.models.request import Request
    
    # Role kontrolü
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    
    # Bu POSM'e ait request'ler var mı kontrol et
    request_count = db.query(Request).filter(Request.posm_id == posm_id).count()
    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu POSM'e ait {request_count} adet talep bulunmaktadır. Önce talepleri silmeniz veya başka bir POSM'e aktarmanız gerekmektedir."
        )
    
    # POSM'i silmeden önce bilgilerini al (audit log için)
    posm = db.query(Posm).filter(Posm.id == posm_id).first()
    if not posm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    posm_service = PosmService(db)
    success = posm_service.delete_posm(posm_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POSM bulunamadı"
        )
    
    # Audit log oluştur
    try:
        from app.services.audit_service import AuditService
        from app.utils.ip_helper import get_client_ip
        audit_service = AuditService(db)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        audit_service.create_log(
            user_id=current_user["id"],
            action="DELETE",
            entity_type="POSM",
            entity_id=posm_id,
            old_values={"name": posm.name, "depot_id": posm.depot_id},
            description=f"POSM silindi: {posm.name}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    return {"success": True, "message": "POSM başarıyla silindi"}


@router.post("/transfer", response_model=PosmTransferResponse)
async def transfer_posm(
    transfer_data: PosmTransferRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """POSM transfer et (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    
    if transfer_data.from_depot_id == transfer_data.to_depot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kaynak ve hedef depo aynı olamaz"
        )
    
    posm_service = PosmService(db)
    try:
        transfer = posm_service.transfer_posm(transfer_data, current_user["id"])
        return transfer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer işlemi başarısız: {str(e)}"
        )


@router.get("/transfers", response_model=List[PosmTransferResponse])
async def get_transfers(
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Transfer geçmişini getir (admin/tech)"""
    if current_user["role"] not in ["admin", "tech"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # Tech kullanıcılar sadece kendi depolarındaki transferleri görebilir
    if current_user["role"] == "tech" and not depot_id:
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        # Tech kullanıcılar için tüm transferleri göster (kendi depolarıyla ilgili)
        # Burada filtreleme yapılabilir ama şimdilik tüm transferleri gösteriyoruz
        pass
    
    posm_service = PosmService(db)
    transfers = posm_service.get_transfers(depot_id=depot_id)
    return transfers
