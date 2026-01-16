from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RefreshRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi"""
    from app.services.audit_service import AuditService
    from app.models.user import User
    
    auth_service = AuthService(db)
    result = auth_service.authenticate(login_data.email, login_data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz e-posta veya şifre",
        )
    
    # Audit log oluştur (başarılı login)
    try:
        user = db.query(User).filter(User.email == login_data.email).first()
        if user:
            from app.utils.ip_helper import get_client_ip
            audit_service = AuditService(db)
            client_ip = get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            audit_service.create_log(
                user_id=user.id,
                action="LOGIN",
                entity_type="User",
                entity_id=user.id,
                description=f"Kullanıcı giriş yaptı: {user.email}",
                ip_address=client_ip,
                user_agent=user_agent
            )
    except Exception as e:
        # Audit log hatası login'i engellemesin
        import logging
        logging.getLogger(__name__).warning(f"Audit log oluşturma hatası: {e}")

    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(refresh_data: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh token ile yeni access/refresh token üret"""
    auth_service = AuthService(db)
    result = auth_service.refresh_tokens(refresh_data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş refresh token",
        )

    return result


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: dict = Depends(AuthService.get_current_user)):
    """Mevcut kullanıcı bilgilerini getir"""
    return current_user
