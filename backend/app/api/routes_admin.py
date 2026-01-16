from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole
from app.models.dealer import Dealer
from app.models.depot import Depot
from app.models.territory import Territory
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.dealer import DealerCreate, DealerUpdate, DealerResponse
from app.schemas.depot import DepotResponse
from app.core.security import get_password_hash
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


# ========== DEPOT YÖNETİMİ ==========

@router.get("/depots", response_model=List[DepotResponse])
async def get_depots(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Tüm depoları listele"""
    depots = db.query(Depot).all()
    return depots


@router.delete("/depots/{depot_id}")
async def delete_depot(
    depot_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Depo sil (admin only)"""
    from app.models.request import Request
    from app.models.user import user_depots
    
    depot = db.query(Depot).filter(Depot.id == depot_id).first()
    if not depot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Depo bulunamadı"
        )
    
    # Bu depoya ait request'ler var mı kontrol et
    request_count = db.query(Request).filter(Request.depot_id == depot_id).count()
    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu depoya ait {request_count} adet talep bulunmaktadır. Önce talepleri silmeniz veya başka bir depoya aktarmanız gerekmektedir."
        )
    
    # Bu depoya ait dealer'lar var mı kontrol et
    dealer_count = db.query(Dealer).filter(Dealer.depot_id == depot_id).count()
    if dealer_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu depoya ait {dealer_count} adet bayi bulunmaktadır. Önce bayileri silmeniz veya başka bir depoya aktarmanız gerekmektedir."
        )
    
    # Bu depoya ait POSM'ler var mı kontrol et
    from app.models.posm import Posm
    posm_count = db.query(Posm).filter(Posm.depot_id == depot_id).count()
    if posm_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu depoya ait {posm_count} adet POSM bulunmaktadır. Önce POSM'leri silmeniz gerekmektedir."
        )
    
    # Bu depoya bağlı kullanıcılar var mı kontrol et (many-to-many)
    user_count = db.query(User).join(user_depots).filter(user_depots.c.depot_id == depot_id).count()
    # Backward compatibility: depot_id ile de kontrol et
    if user_count == 0:
        user_count = db.query(User).filter(User.depot_id == depot_id).count()
    
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu depoya bağlı {user_count} adet kullanıcı bulunmaktadır. Önce kullanıcıların depo bağlantılarını kaldırmanız gerekmektedir."
        )
    
    # Transfer kayıtlarını kontrol et
    from app.models.posm_transfer import PosmTransfer
    transfer_count = db.query(PosmTransfer).filter(
        (PosmTransfer.from_depot_id == depot_id) | (PosmTransfer.to_depot_id == depot_id)
    ).count()
    if transfer_count > 0:
        # Transfer kayıtları varsa uyarı ver ama silmeye izin ver (opsiyonel)
        # Veya transfer kayıtlarını da silmek isteyebilirsiniz
        pass
    
    # Audit log oluştur (silmeden önce)
    try:
        from app.services.audit_service import AuditService
        from app.utils.ip_helper import get_client_ip
        audit_service = AuditService(db)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        audit_service.create_log(
            user_id=current_user["id"],
            action="DELETE",
            entity_type="Depot",
            entity_id=depot_id,
            old_values={"name": depot.name, "code": depot.code},
            description=f"Depo silindi: {depot.name} ({depot.code})",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    db.delete(depot)
    db.commit()
    
    return {"message": "Depo başarıyla silindi"}


# ========== ROL YÖNETİMİ ==========

@router.get("/roles")
async def get_roles(
    current_user: dict = Depends(require_admin)
):
    """Tüm roller ve yetkileri listele"""
    roles = [
        {
            "value": "user",
            "label": "Kullanıcı",
            "permissions": [
                "Kendi taleplerini görüntüleme",
                "Yeni talep oluşturma",
                "Kendi taleplerini güncelleme"
            ]
        },
        {
            "value": "tech",
            "label": "Teknik Sorumlu",
            "permissions": [
                "Tüm talepleri görüntüleme",
                "Talepleri güncelleme",
                "POSM stok yönetimi",
                "Talep durumu değiştirme"
            ]
        },
        {
            "value": "admin",
            "label": "Yönetici",
            "permissions": [
                "Tüm yetkiler",
                "Kullanıcı yönetimi",
                "Bayi yönetimi",
                "Toplu bayi import",
                "Rol yönetimi",
                "Tüm talepleri görüntüleme ve yönetme"
            ]
        }
    ]
    return {"roles": roles}


# ========== KULLANICI YÖNETİMİ ==========

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Tüm kullanıcıları listele (depo filtresi ile)"""
    query = db.query(User)
    
    if depot_id:
        # Filter by depot_id (backward compatibility) or many-to-many relationship
        from app.models.user import user_depots
        query = query.outerjoin(user_depots).filter(
            (User.depot_id == depot_id) | (user_depots.c.depot_id == depot_id)
        ).distinct()
    
    users = query.all()
    
    # Include depot_ids in response
    result = []
    for user in users:
        user_dict = UserResponse.model_validate(user).model_dump()
        user_dict["depot_ids"] = [d.id for d in user.depots]
        result.append(UserResponse(**user_dict))
    
    return result


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Yeni kullanıcı oluştur"""
    # Email kontrolü
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanılıyor"
        )
    
    # Depot kontrolü
    if user_data.depot_id:
        depot = db.query(Depot).filter(Depot.id == user_data.depot_id).first()
        if not depot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Depo bulunamadı"
            )
    
    # Rol kontrolü
    valid_roles = [r.value for r in UserRole]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geçersiz rol. Geçerli roller: {', '.join(valid_roles)}"
        )
    
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        depot_id=user_data.depot_id  # Backward compatibility
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Set many-to-many depot relationships
    if user_data.depot_ids:
        for depot_id in user_data.depot_ids:
            depot = db.query(Depot).filter(Depot.id == depot_id).first()
            if depot:
                new_user.depots.append(depot)
        db.commit()
        db.refresh(new_user)
    
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
            entity_type="User",
            entity_id=new_user.id,
            new_values={"name": new_user.name, "email": new_user.email, "role": new_user.role},
            description=f"Yeni kullanıcı oluşturuldu: {new_user.email}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    # Set depot_ids in response
    response_user = UserResponse.model_validate(new_user)
    response_user.depot_ids = [d.id for d in new_user.depots]
    return response_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Kullanıcı detaylarını getir"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Include depot_ids in response
    response_user = UserResponse.model_validate(user)
    response_user.depot_ids = [d.id for d in user.depots]
    return response_user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Kullanıcı güncelle"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Eski değerleri kaydet (audit log için - güncellemeden önce)
    old_values = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "depot_id": user.depot_id
    }
    
    # Email kontrolü (eğer değiştiriliyorsa)
    if user_data.email and user_data.email != user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu e-posta adresi zaten kullanılıyor"
            )
        user.email = user_data.email
    
    # Diğer alanları güncelle
    if user_data.name:
        user.name = user_data.name
    if user_data.role:
        valid_roles = [r.value for r in UserRole]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz rol. Geçerli roller: {', '.join(valid_roles)}"
            )
        user.role = user_data.role
    if user_data.depot_id is not None:
        if user_data.depot_id:
            depot = db.query(Depot).filter(Depot.id == user_data.depot_id).first()
            if not depot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Depo bulunamadı"
                )
        user.depot_id = user_data.depot_id  # Backward compatibility
    
    # Update many-to-many depot relationships
    if user_data.depot_ids is not None:
        # Clear existing depots
        user.depots.clear()
        # Add new depots
        for depot_id in user_data.depot_ids:
            depot = db.query(Depot).filter(Depot.id == depot_id).first()
            if depot:
                user.depots.append(depot)
    
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    # Yeni değerleri kaydet (audit log için)
    new_values = {}
    if user_data.name:
        new_values["name"] = user_data.name
    if user_data.email:
        new_values["email"] = user_data.email
    if user_data.role:
        new_values["role"] = user_data.role
    
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
            entity_type="User",
            entity_id=user_id,
            old_values=old_values,
            new_values=new_values if new_values else None,
            description=f"Kullanıcı güncellendi: {user.email}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    # Set depot_ids in response
    response_user = UserResponse.model_validate(user)
    response_user.depot_ids = [d.id for d in user.depots]
    return response_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Kullanıcı sil"""
    from app.models.request import Request
    
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı silemezsiniz"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Bu kullanıcıya ait request'ler var mı kontrol et
    request_count = db.query(Request).filter(Request.user_id == user_id).count()
    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu kullanıcıya ait {request_count} adet talep bulunmaktadır. Önce talepleri silmeniz veya başka bir kullanıcıya aktarmanız gerekmektedir."
        )
    
    # Bu kullanıcının tamamladığı request'ler var mı kontrol et (completed_by)
    completed_count = db.query(Request).filter(Request.completed_by == user_id).count()
    if completed_count > 0:
        # Tamamlanan request'lerde completed_by'i null yap
        db.query(Request).filter(Request.completed_by == user_id).update({"completed_by": None})
    
    # Bu kullanıcının güncellediği request'ler var mı kontrol et (updated_by)
    updated_count = db.query(Request).filter(Request.updated_by == user_id).count()
    if updated_count > 0:
        # Güncellenen request'lerde updated_by'i null yap
        db.query(Request).filter(Request.updated_by == user_id).update({"updated_by": None})
    
    # Audit log oluştur (silmeden önce)
    try:
        from app.services.audit_service import AuditService
        from app.utils.ip_helper import get_client_ip
        audit_service = AuditService(db)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        audit_service.create_log(
            user_id=current_user["id"],
            action="DELETE",
            entity_type="User",
            entity_id=user_id,
            old_values={"name": user.name, "email": user.email, "role": user.role},
            description=f"Kullanıcı silindi: {user.email}",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Kullanıcı başarıyla silindi"}


# ========== BAYİ YÖNETİMİ ==========

@router.get("/dealers", response_model=List[DealerResponse])
async def get_dealers(
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Tüm bayileri listele (depo filtresi ile)"""
    query = db.query(Dealer)
    if depot_id:
        query = query.filter(Dealer.depot_id == depot_id)
    dealers = query.all()
    return dealers


@router.post("/dealers", response_model=DealerResponse)
async def create_dealer(
    dealer_data: DealerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Yeni bayi oluştur"""
    # Depot kontrolü
    if dealer_data.depot_id:
        depot = db.query(Depot).filter(Depot.id == dealer_data.depot_id).first()
        if not depot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Depo bulunamadı"
            )
    
    # Territory kontrolü
    if dealer_data.territory_id:
        territory = db.query(Territory).filter(Territory.id == dealer_data.territory_id).first()
        if not territory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Territory bulunamadı"
            )
    
    # Aynı depo içinde kod unique olmalı
    existing = db.query(Dealer).filter(
        Dealer.code == dealer_data.code,
        Dealer.depot_id == dealer_data.depot_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu depo içinde bu bayi kodu zaten kullanılıyor"
        )
    
    new_dealer = Dealer(
        code=dealer_data.code,
        name=dealer_data.name,
        territory_id=dealer_data.territory_id,
        depot_id=dealer_data.depot_id,
        latitude=dealer_data.latitude,
        longitude=dealer_data.longitude
    )
    
    db.add(new_dealer)
    db.commit()
    db.refresh(new_dealer)
    
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
            entity_type="Dealer",
            entity_id=new_dealer.id,
            new_values={"code": new_dealer.code, "name": new_dealer.name, "depot_id": new_dealer.depot_id},
            description=f"Yeni bayi oluşturuldu: {new_dealer.name} ({new_dealer.code})",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    return new_dealer


@router.get("/dealers/{dealer_id}", response_model=DealerResponse)
async def get_dealer(
    dealer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Bayi detaylarını getir"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bayi bulunamadı"
        )
    return dealer


@router.patch("/dealers/{dealer_id}", response_model=DealerResponse)
async def update_dealer(
    dealer_id: int,
    dealer_data: DealerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Bayi güncelle"""
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bayi bulunamadı"
        )
    
    # Eski değerleri kaydet (audit log için - güncellemeden önce)
    old_values = {
        "code": dealer.code,
        "name": dealer.name,
        "depot_id": dealer.depot_id,
        "territory_id": dealer.territory_id
    }
    
    # Depot kontrolü
    if dealer_data.depot_id is not None:
        if dealer_data.depot_id:
            depot = db.query(Depot).filter(Depot.id == dealer_data.depot_id).first()
            if not depot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Depo bulunamadı"
                )
        dealer.depot_id = dealer_data.depot_id
    
    # Territory kontrolü
    if dealer_data.territory_id is not None:
        if dealer_data.territory_id:
            territory = db.query(Territory).filter(Territory.id == dealer_data.territory_id).first()
            if not territory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Territory bulunamadı"
                )
        dealer.territory_id = dealer_data.territory_id
    
    # Kod kontrolü (eğer değiştiriliyorsa)
    if dealer_data.code and dealer_data.code != dealer.code:
        depot_id = dealer_data.depot_id if dealer_data.depot_id is not None else dealer.depot_id
        existing = db.query(Dealer).filter(
            Dealer.code == dealer_data.code,
            Dealer.depot_id == depot_id,
            Dealer.id != dealer_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu depo içinde bu bayi kodu zaten kullanılıyor"
            )
        dealer.code = dealer_data.code
    
    # Diğer alanları güncelle
    if dealer_data.name:
        dealer.name = dealer_data.name
    if dealer_data.latitude is not None:
        dealer.latitude = dealer_data.latitude
    if dealer_data.longitude is not None:
        dealer.longitude = dealer_data.longitude
    
    db.commit()
    db.refresh(dealer)
    
    # Yeni değerleri kaydet (audit log için)
    new_values = {}
    if dealer_data.code:
        new_values["code"] = dealer_data.code
    if dealer_data.name:
        new_values["name"] = dealer_data.name
    if dealer_data.depot_id is not None:
        new_values["depot_id"] = dealer_data.depot_id
    
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
            entity_type="Dealer",
            entity_id=dealer_id,
            old_values=old_values,
            new_values=new_values if new_values else None,
            description=f"Bayi güncellendi: {dealer.name} ({dealer.code})",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    return dealer


@router.delete("/dealers/{dealer_id}")
async def delete_dealer(
    dealer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Bayi sil"""
    from app.models.request import Request
    
    dealer = db.query(Dealer).filter(Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bayi bulunamadı"
        )
    
    # Bu bayiye ait request'ler var mı kontrol et
    request_count = db.query(Request).filter(Request.dealer_id == dealer_id).count()
    if request_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu bayiye ait {request_count} adet talep bulunmaktadır. Önce talepleri silmeniz veya başka bir bayiye aktarmanız gerekmektedir."
        )
    
    # Audit log oluştur (silmeden önce)
    try:
        from app.services.audit_service import AuditService
        from app.utils.ip_helper import get_client_ip
        audit_service = AuditService(db)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        audit_service.create_log(
            user_id=current_user["id"],
            action="DELETE",
            entity_type="Dealer",
            entity_id=dealer_id,
            old_values={"code": dealer.code, "name": dealer.name, "depot_id": dealer.depot_id},
            description=f"Bayi silindi: {dealer.name} ({dealer.code})",
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")
    
    db.delete(dealer)
    db.commit()
    
    return {"message": "Bayi başarıyla silindi"}


# ========== TOPLU BAYİ İMPORT ==========

@router.post("/dealers/bulk-import")
async def bulk_import_dealers(
    file: UploadFile = File(...),
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Excel/CSV dosyasından toplu bayi import"""
    if not depot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="depot_id parametresi gereklidir"
        )
    
    # Depot kontrolü
    depot = db.query(Depot).filter(Depot.id == depot_id).first()
    if not depot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Depo bulunamadı"
        )
    
    # Dosya içeriğini oku
    contents = await file.read()
    
    try:
        # Excel veya CSV dosyasını parse et
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(contents))
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Desteklenen formatlar: .xlsx, .xls, .csv"
            )
        
        # Beklenen kolonlar: Bayi Kodu, Bayi Adı, Territory (opsiyonel), Latitude (opsiyonel), Longitude (opsiyonel)
        required_cols = ["Bayi Kodu", "Bayi Adı"]
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Eksik kolon: {col}. Gerekli kolonlar: {', '.join(required_cols)}"
                )
        
        imported = 0
        updated = 0
        errors = []
        
        # Excel dosyasındaki duplicate'leri temizle (aynı code + depot_id kombinasyonu)
        # Son görünen değeri kullan (daha güncel olabilir)
        seen_combinations = {}
        df_cleaned = []
        for idx, row in df.iterrows():
            code = str(row["Bayi Kodu"]).strip() if pd.notna(row.get("Bayi Kodu")) else ""
            if code:
                key = (code, depot_id)
                # Eğer daha önce görüldüyse, eski kaydı kaldır ve yenisini ekle
                if key in seen_combinations:
                    # Eski kaydı bul ve kaldır
                    old_idx = seen_combinations[key]
                    df_cleaned = [(i, r) for i, r in df_cleaned if i != old_idx]
                    errors.append(f"Satır {old_idx + 2}: Duplicate bayi kodu '{code}' - son görünen değer kullanıldı")
                seen_combinations[key] = idx
                df_cleaned.append((idx, row))
        
        # Session içinde eklenen kayıtları takip et (aynı batch içinde duplicate'leri önlemek için)
        session_added_keys = set()
        
        # Temizlenmiş verileri işle
        for idx, row in df_cleaned:
            try:
                code = str(row["Bayi Kodu"]).strip()
                name = str(row["Bayi Adı"]).strip()
                
                if not code or not name:
                    errors.append(f"Satır {idx + 2}: Kod veya isim boş")
                    continue
                
                key = (code, depot_id)
                
                # Önce session içinde eklenen kayıtları kontrol et
                if key in session_added_keys:
                    errors.append(f"Satır {idx + 2}: Duplicate bayi kodu '{code}' aynı import içinde - atlandı")
                    continue
                
                # Territory bul (eğer varsa)
                territory_id = None
                if "Territory" in df.columns and pd.notna(row.get("Territory")):
                    territory_name = str(row["Territory"]).strip()
                    territory = db.query(Territory).filter(Territory.name == territory_name).first()
                    if territory:
                        territory_id = territory.id
                
                # Latitude/Longitude
                latitude = None
                longitude = None
                if "Latitude" in df.columns and pd.notna(row.get("Latitude")):
                    try:
                        latitude = float(str(row["Latitude"]).replace(",", "."))
                    except:
                        pass
                if "Longitude" in df.columns and pd.notna(row.get("Longitude")):
                    try:
                        longitude = float(str(row["Longitude"]).replace(",", "."))
                    except:
                        pass
                
                # Mevcut bayi kontrolü (veritabanında)
                existing = db.query(Dealer).filter(
                    Dealer.code == code,
                    Dealer.depot_id == depot_id
                ).first()
                
                if existing:
                    # Güncelle
                    existing.name = name
                    existing.territory_id = territory_id
                    existing.latitude = latitude
                    existing.longitude = longitude
                    updated += 1
                else:
                    # Yeni ekle
                    new_dealer = Dealer(
                        code=code,
                        name=name,
                        territory_id=territory_id,
                        depot_id=depot_id,
                        latitude=latitude,
                        longitude=longitude
                    )
                    db.add(new_dealer)
                    session_added_keys.add(key)  # Session'a eklenen kayıtları takip et
                    imported += 1
                
            except Exception as e:
                errors.append(f"Satır {idx + 2}: {str(e)[:100]}")
                continue
        
        # Tüm değişiklikleri tek seferde commit et
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # UniqueViolation hatasını daha anlaşılır hale getir
            error_msg = str(e)
            if "UniqueViolation" in error_msg or "duplicate key" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Import hatası: Aynı bayi kodu ve depo kombinasyonu zaten mevcut. Lütfen Excel dosyasındaki duplicate kayıtları kontrol edin. Detay: {error_msg[:200]}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Veritabanı hatası: {str(e)}"
            )
        
        return {
            "message": "Toplu import tamamlandı",
            "imported": imported,
            "updated": updated,
            "errors": errors[:10]  # İlk 10 hatayı göster
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import hatası: {str(e)}"
        )
