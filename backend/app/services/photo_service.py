import os
import uuid
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.photo import Photo
from app.models.request import Request
from app.core.config import settings


class PhotoService:
    def __init__(self, db: Session):
        self.db = db

    def upload_photos(self, request_id: int, files: List[UploadFile]) -> List[dict]:
        """Fotoğrafları yükle"""
        # Request'in var olduğunu kontrol et
        request = self.db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise ValueError("Talep bulunamadı")
        
        # Uploads klasörünü oluştur
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        uploaded_photos = []
        
        for file in files:
            # Dosya boyutu kontrolü
            file.file.seek(0, 2)  # Dosyanın sonuna git
            file_size = file.file.tell()
            file.file.seek(0)  # Başa dön
            
            if file_size > settings.MAX_UPLOAD_SIZE:
                raise ValueError(f"Dosya boyutu çok büyük. Maksimum boyut: {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB")
            
            # Dosya tipi kontrolü (opsiyonel - sadece resim dosyaları)
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                raise ValueError(f"Geçersiz dosya tipi. İzin verilen formatlar: {', '.join(allowed_extensions)}")
            
            # Dosya adını güvenli hale getir
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Dosyayı kaydet
            with open(file_path, "wb") as f:
                content = file.file.read()
                f.write(content)
            
            # Database'e kaydet
            photo = Photo(
                request_id=request_id,
                path_or_url=f"/uploads/{unique_filename}",
                file_name=file.filename,
                mime_type=file.content_type
            )
            
            self.db.add(photo)
            uploaded_photos.append({
                "url": photo.path_or_url,
                "name": photo.file_name,
                "id": photo.id
            })
        
        self.db.commit()
        
        return uploaded_photos

    def get_request_photos(self, request_id: int) -> List[dict]:
        """Talep fotoğraflarını getir"""
        photos = self.db.query(Photo).filter(Photo.request_id == request_id).all()
        
        return [{
            "url": p.path_or_url,
            "name": p.file_name,
            "id": p.id
        } for p in photos]
