from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.photo_service import PhotoService
from app.services.request_service import RequestService
import os

router = APIRouter()


@router.post("/requests/{request_id}")
async def upload_photos(
    request_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Fotoğraf yükle"""
    from app.models.request import Request
    
    # Talep var mı kontrol et
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talep bulunamadı"
        )
    
    # Yetki kontrolü
    if current_user["role"] == "admin":
        # Admin her talebe fotoğraf ekleyebilir
        pass
    elif current_user["role"] == "tech":
        # Tech kullanıcılar: Kendi depolarındaki taleplere fotoğraf ekleyebilir
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        
        if request.depot_id and request.depot_id not in user_depot_ids:
            # Kendi talebi değilse ve kendi deposunda değilse erişim yok
            request_service = RequestService(db)
            user_requests = request_service.get_user_requests(current_user["email"])
            if request_id not in [r.id for r in user_requests]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu talebe fotoğraf ekleme yetkiniz yok"
                )
    else:
        # Normal kullanıcılar: Sadece kendi taleplerine fotoğraf ekleyebilir
        request_service = RequestService(db)
        user_requests = request_service.get_user_requests(current_user["email"])
        if request_id not in [r.id for r in user_requests]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu talebe fotoğraf ekleme yetkiniz yok"
            )
    
    photo_service = PhotoService(db)
    
    try:
        uploaded_photos = photo_service.upload_photos(request_id, files)
        return {
            "success": True,
            "photos": uploaded_photos
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/requests/{request_id}")
async def get_request_photos(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Talep fotoğraflarını getir"""
    from app.models.request import Request
    
    # Talep var mı kontrol et
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talep bulunamadı"
        )
    
    # Yetki kontrolü
    if current_user["role"] == "admin":
        # Admin her talebin fotoğraflarını görebilir
        pass
    elif current_user["role"] == "tech":
        # Tech kullanıcılar: Kendi depolarındaki taleplerin fotoğraflarını görebilir
        user_depot_ids = current_user.get("depot_ids", [])
        if not user_depot_ids and current_user.get("depot_id"):
            user_depot_ids = [current_user["depot_id"]]
        
        if request.depot_id and request.depot_id not in user_depot_ids:
            # Kendi talebi değilse ve kendi deposunda değilse erişim yok
            request_service = RequestService(db)
            user_requests = request_service.get_user_requests(current_user["email"])
            if request_id not in [r.id for r in user_requests]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu talebin fotoğraflarına erişim yetkiniz yok"
                )
    else:
        # Normal kullanıcılar: Sadece kendi taleplerinin fotoğraflarını görebilir
        request_service = RequestService(db)
        user_requests = request_service.get_user_requests(current_user["email"])
        if request_id not in [r.id for r in user_requests]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu talebin fotoğraflarına erişim yetkiniz yok"
            )
    
    photo_service = PhotoService(db)
    photos = photo_service.get_request_photos(request_id)
    
    return {"photos": photos}


@router.get("/files/{filename}")
async def get_photo_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Fotoğraf dosyasını getir"""
    from app.core.config import settings
    from app.models.photo import Photo
    
    # Path traversal saldırısını önle
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz dosya adı"
        )
    
    # Dosya adını normalize et (sadece dosya adı, path değil)
    filename = os.path.basename(filename)
    
    # Veritabanında fotoğraf kaydını kontrol et
    photo = db.query(Photo).filter(Photo.filename == filename).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fotoğraf bulunamadı"
        )
    
    # Yetki kontrolü: Kullanıcı sadece kendi taleplerinin fotoğraflarını görebilir (admin/tech hariç)
    if current_user["role"] not in ["admin", "tech"]:
        request_service = RequestService(db)
        user_requests = request_service.get_user_requests(current_user["email"])
        if photo.request_id not in [r.id for r in user_requests]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu fotoğrafa erişim yetkiniz yok"
            )
    elif current_user["role"] == "tech":
        # Tech kullanıcılar: Kendi depolarındaki taleplerin fotoğraflarını görebilir
        from app.models.request import Request
        request = db.query(Request).filter(Request.id == photo.request_id).first()
        if request:
            user_depot_ids = current_user.get("depot_ids", [])
            if not user_depot_ids and current_user.get("depot_id"):
                user_depot_ids = [current_user["depot_id"]]
            
            if request.depot_id and request.depot_id not in user_depot_ids:
                # Kendi talebi değilse ve kendi deposunda değilse erişim yok
                user_requests = request_service.get_user_requests(current_user["email"])
                if photo.request_id not in [r.id for r in user_requests]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Bu fotoğrafa erişim yetkiniz yok"
                    )
    
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Path traversal kontrolü (ikinci kez)
    real_path = os.path.realpath(file_path)
    real_upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(real_upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz dosya yolu"
        )
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosya bulunamadı"
        )
    
    return FileResponse(file_path)
