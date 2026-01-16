from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi import Request as FastAPIRequest
from app.db.session import SessionLocal, get_db
from app.models.request import Request, RequestStatus
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.request_service import RequestService
from app.schemas.request import (
    RequestCreate, RequestResponse, RequestDetailResponse,
    RequestUpdate, RequestStatsResponse
)

router = APIRouter()


@router.get("/", response_model=list[RequestResponse])
async def get_requests(
    mine: bool = Query(False),
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Talepleri getir (kullanıcının kendi talepleri veya tüm talepler, depot filtresi ile)"""
    request_service = RequestService(db)
    
    # Depot filtresi: Kullanıcının depot_id'si varsa ve parametre yoksa onu kullan
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        user_depot_ids = [current_user["depot_id"]]
    
    if not depot_id and user_depot_ids:
        depot_id = user_depot_ids[0]  # İlk depo varsayılan olarak
    
    if mine:
        # Kullanıcının kendi talepleri
        # Tech kullanıcılar için kendi depolarındaki talepleri de dahil et
        include_depot = current_user["role"] in ["tech", "admin"]
        return request_service.get_user_requests(
            current_user["email"], 
            depot_id=depot_id,
            include_depot_requests=include_depot
        )
    else:
        # Tüm talepler (sadece admin)
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için admin yetkisi gereklidir"
            )
        return request_service.get_all_requests(depot_id=depot_id)


@router.get("/stats", response_model=RequestStatsResponse)
async def get_request_stats(
    depot_id: Optional[int] = Query(None),
    user_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Talep istatistiklerini getir (depot filtresi ile) - Tüm kullanıcılar için"""
    request_service = RequestService(db)
    
    # Eğer user_email parametresi verilmişse onu kullan, yoksa:
    # Admin ise tüm istatistikler, diğerleri sadece kendi istatistikleri
    if user_email is None:
        user_email = None if current_user["role"] == "admin" else current_user["email"]
    else:
        # user_email parametresi verilmişse, sadece admin başka kullanıcıların istatistiklerini görebilir
        if current_user["role"] != "admin" and user_email != current_user["email"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Başka kullanıcıların istatistiklerini görme yetkiniz yok"
            )
    
    # Depot filtresi: Kullanıcının depot_id'si varsa ve parametre yoksa onu kullan
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        user_depot_ids = [current_user["depot_id"]]
    
    # Depot ID kontrolü: Admin olmayan kullanıcılar sadece kendi depolarını seçebilir
    if depot_id and current_user["role"] != "admin":
        if depot_id not in user_depot_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu depo için yetkiniz yok"
            )
    
    if not depot_id and user_depot_ids and current_user["role"] != "admin":
        depot_id = user_depot_ids[0]  # İlk depo varsayılan olarak
    
    return request_service.get_request_stats(user_email=user_email, depot_id=depot_id)


@router.get("/{request_id}", response_model=RequestDetailResponse)
async def get_request_details(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Talep detaylarını getir"""
    request_service = RequestService(db)
    
    # Önce talebi getir
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talep bulunamadı"
        )
    
    # Yetki kontrolü: Admin tüm talepleri görebilir
    # Tech kullanıcılar kendi depolarındaki talepleri görebilir
    # Normal kullanıcılar sadece kendi taleplerini görebilir
    if current_user["role"] != "admin":
        if current_user["role"] == "tech":
            # Tech kullanıcılar: Kendi depolarındaki talepleri görebilir
            user_depot_ids = current_user.get("depot_ids", [])
            if not user_depot_ids and current_user.get("depot_id"):
                user_depot_ids = [current_user["depot_id"]]
            
            # Talep kendi depolarından birinde mi kontrol et
            if request.depot_id and request.depot_id not in user_depot_ids:
                # Kendi talebi değilse erişim yok
                user_requests = request_service.get_user_requests(current_user["email"])
                if request_id not in [r.id for r in user_requests]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Bu talebe erişim yetkiniz yok"
                    )
        else:
            # Normal kullanıcılar: Sadece kendi taleplerini görebilir
            user_requests = request_service.get_user_requests(current_user["email"])
            if request_id not in [r.id for r in user_requests]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu talebe erişim yetkiniz yok"
                )
    
    # Detayları getir
    request_detail = request_service.get_request_by_id(request_id)
    return request_detail


@router.post("/", response_model=dict)
async def create_request(
    request_data: RequestCreate,
    background_tasks: BackgroundTasks,
    request: FastAPIRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Yeni talep oluştur"""
    from app.models.dealer import Dealer
    
    request_service = RequestService(db)
    
    # dealer_code varsa dealer_id'ye çevir
    if request_data.dealer_code and (not request_data.dealer_id or request_data.dealer_id == 0):
        dealer = db.query(Dealer).filter(Dealer.code == request_data.dealer_code).first()
        if not dealer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bayi bulunamadı"
            )
        request_data.dealer_id = dealer.id
    
    if not request_data.dealer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bayi bilgisi gerekli"
        )
    
    try:
        # Dealer'ı kontrol et ve depot_id'yi al
        dealer = db.query(Dealer).filter(Dealer.id == request_data.dealer_id).first()
        if not dealer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bayi bulunamadı"
            )
        
        # Kullanıcının depot_id'si ile dealer'ın depot_id'si uyumlu mu kontrol et (opsiyonel - sadece uyarı)
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        
        if dealer.depot_id and user_depot_ids and dealer.depot_id not in user_depot_ids:
            # Uyarı: Kullanıcı farklı bir depodaki bayi için talep oluşturuyor
            # Bu durumda devam edebilir ama log'a kaydedilebilir
            pass
        
        new_request = request_service.create_request(
            user_id=current_user["id"],
            request_data=request_data
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
                action="CREATE",
                entity_type="Request",
                entity_id=new_request.id,
                new_values={"status": new_request.status, "job_type": new_request.job_type, "dealer_id": new_request.dealer_id},
                description=f"Yeni talep oluşturuldu: {new_request.id}",
                ip_address=client_ip,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"⚠️ Audit log oluşturma hatası: {e}")
        
        # Talep oluşturulduğunda bildirim gönder (background task)
        def send_notifications():
            try:
                from app.services.notification_service import NotificationService
                from app.models.user import User
                import asyncio
                
                bg_db = SessionLocal()
                try:
                    notification_service = NotificationService(bg_db)
                    
                    # Request'i yeniden yükle (detached instance için)
                    request = bg_db.query(Request).filter(Request.id == new_request.id).first()
                    if not request:
                        return
                    
                    # Talep oluşturana bildirim gönder
                    request_user = bg_db.query(User).filter(User.id == current_user["id"]).first()
                    if request_user and request_user.email:
                        try:
                            asyncio.run(notification_service.notify_request_created(
                                request,
                                request_user
                            ))
                        except Exception as e:
                            print(f"⚠️ Talep oluşturana bildirim hatası: {e}")
                    
                    # Aynı depodaki teknik sorumlulara bildirim gönder (many-to-many)
                    if request.depot_id:
                        from app.models.user import user_depots
                        tech_users = bg_db.query(User).join(user_depots).filter(
                            user_depots.c.depot_id == request.depot_id,
                            User.role.in_(["tech", "admin"])
                        ).all()
                        
                        # Backward compatibility: depot_id ile de kontrol et
                        if not tech_users:
                            tech_users = bg_db.query(User).filter(
                                User.depot_id == request.depot_id,
                                User.role.in_(["tech", "admin"])
                            ).all()
                        
                        for tech_user in tech_users:
                            if tech_user.id != current_user["id"] and tech_user.email:
                                try:
                                    asyncio.run(notification_service.notify_new_request_to_tech(
                                        request,
                                        tech_user,
                                        request_user
                                    ))
                                except Exception as e:
                                    print(f"⚠️ Teknik sorumluya bildirim hatası (user {tech_user.id}): {e}")
                finally:
                    bg_db.close()
            except Exception as e:
                print(f"⚠️ Bildirim gönderme hatası: {e}")
                import traceback
                traceback.print_exc()
        
        background_tasks.add_task(send_notifications)
        
        return {
            "success": True,
            "requestId": new_request.id
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{request_id}", response_model=RequestResponse)
async def update_request(
    request_id: int,
    update_data: RequestUpdate,
    background_tasks: BackgroundTasks,
    request: FastAPIRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Talep güncelle (admin/tech only)"""
    # Role kontrolü
    if current_user["role"] not in ["admin", "tech"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok"
        )
    
    # Eğer durum "Tamamlandı" olarak güncelleniyorsa, fotoğraf ve tarih kontrolü yap
    if update_data.status == "Tamamlandı":
        from app.services.photo_service import PhotoService
        photo_service = PhotoService(db)
        photos = photo_service.get_request_photos(request_id)
        if len(photos) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İş tamamlandı olarak işaretlenmeden önce en az bir fotoğraf yüklenmelidir"
            )
        # Tamamlanma tarihi kontrolü
        if not update_data.completed_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İş tamamlandı olarak işaretlenmeden önce tamamlanma tarihi belirtilmelidir"
            )
    
    request_service = RequestService(db)
    # Eski durumu kaydet (bildirim için)
    old_request = db.query(Request).filter(Request.id == request_id).first()
    if not old_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talep bulunamadı"
        )
    old_status = old_request.status
    old_planned_date = old_request.planned_date
    
    # Eski değerleri kaydet (audit log için)
    old_values = {
        "status": old_request.status,
        "planned_date": old_request.planned_date.isoformat() if old_request.planned_date else None,
        "priority": old_request.priority,
        "completed_date": old_request.completed_date.isoformat() if old_request.completed_date else None
    }
    
    try:
        updated_request = request_service.update_request(
            request_id=request_id,
            update_data=update_data,
            updated_by_id=current_user["id"]
        )
    except ValueError as e:
        # POSM stok hatası gibi validasyon hataları
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not updated_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talep bulunamadı"
        )
    
    # Yeni değerleri kaydet (audit log için)
    new_values = {}
    if update_data.status:
        new_values["status"] = update_data.status
    if update_data.planned_date:
        new_values["planned_date"] = update_data.planned_date.isoformat()
    if update_data.priority:
        new_values["priority"] = update_data.priority
    if update_data.completed_date:
        new_values["completed_date"] = update_data.completed_date.isoformat()
    
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
            entity_type="Request",
            entity_id=request_id,
            old_values=old_values,
            new_values=new_values if new_values else None,
            description=f"Talep güncellendi: {request_id}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"⚠️ Audit log oluşturma hatası: {e}")
    
    # Bildirim gönder (background task)
    def send_update_notifications():
        try:
            from app.services.notification_service import NotificationService
            from app.models.user import User
            import asyncio
            
            bg_db = SessionLocal()
            try:
                notification_service = NotificationService(bg_db)
                
                # Request'i yeniden yükle
                request = bg_db.query(Request).filter(Request.id == request_id).first()
                if not request:
                    return
                
                updated_by_user = bg_db.query(User).filter(User.id == current_user["id"]).first()
                if not updated_by_user:
                    return
                
                changes = {}
                if update_data.status and update_data.status != old_status:
                    changes["status"] = update_data.status
                if update_data.planned_date and update_data.planned_date != old_planned_date:
                    changes["planned_date"] = update_data.planned_date.strftime("%d.%m.%Y")
                if update_data.job_done_desc:
                    changes["job_done_desc"] = True
                
                # Durum değişiklikleri için özel bildirimler
                if update_data.status == RequestStatus.TAKVIME_EKLENDI.value and old_status == RequestStatus.BEKLEMEDE.value:
                    if updated_by_user and request.planned_date:
                        try:
                            asyncio.run(notification_service.notify_request_planned(
                                request,
                                request.planned_date.strftime("%d.%m.%Y"),
                                updated_by_user
                            ))
                        except Exception as e:
                            print(f"⚠️ Planlama bildirimi hatası: {e}")
                elif update_data.status == RequestStatus.TAMAMLANDI.value and old_status != RequestStatus.TAMAMLANDI.value:
                    if updated_by_user and request.completed_date:
                        try:
                            asyncio.run(notification_service.notify_request_completed(
                                request,
                                request.completed_date.strftime("%d.%m.%Y"),
                                updated_by_user
                            ))
                        except Exception as e:
                            print(f"⚠️ Tamamlanma bildirimi hatası: {e}")
                elif changes:
                    # Diğer güncellemeler için genel bildirim
                    try:
                        asyncio.run(notification_service.notify_request_updated(
                            request,
                            updated_by_user,
                            changes
                        ))
                    except Exception as e:
                        print(f"⚠️ Güncelleme bildirimi hatası: {e}")
            finally:
                bg_db.close()
        except Exception as e:
            print(f"⚠️ Bildirim gönderme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    background_tasks.add_task(send_update_notifications)
    
    return request_service._to_response(updated_request)
