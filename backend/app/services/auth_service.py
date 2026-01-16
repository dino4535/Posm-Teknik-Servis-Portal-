from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse

security = HTTPBearer()


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    # --------- Public methods ---------

    def authenticate(self, email: str, password: str) -> Optional[TokenResponse]:
        """
        Kullanıcıyı e-posta/şifre ile doğrular ve access/refresh token üretir.
        """
        user = self.db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            return None

        return self._create_token_response(user)

    def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        """
        Refresh token'dan yeni access/refresh token üretir.
        """
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return None

        return self._create_token_response(user)

    # --------- Static dependency helpers ---------

    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
    ) -> dict:
        """
        Authorization header'daki access token'dan kullanıcıyı çözer.
        """
        token = credentials.credentials
        payload = decode_token(token)

        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz token",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token'da kullanıcı bilgisi bulunamadı",
            )

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı bulunamadı",
            )

        # Get user's depot IDs (many-to-many relationship)
        depot_ids = [depot.id for depot in user.depots] if user.depots else []
        # If no depots in many-to-many, fall back to legacy depot_id
        if not depot_ids and user.depot_id:
            depot_ids = [user.depot_id]
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "depot_id": user.depot_id,  # Backward compatibility
            "depot_ids": depot_ids,  # New: list of depot IDs
        }

    # --------- Internal helpers ---------

    @staticmethod
    def _create_token_response(user: User) -> TokenResponse:
        """
        Verilen kullanıcı için access ve refresh token üretir.
        """
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value if hasattr(user.role, "value") else user.role,
            }
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role.value if hasattr(user.role, "value") else user.role,
            ),
        )
