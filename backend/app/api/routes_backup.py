from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService
from app.core.config import settings
import os
from datetime import datetime

router = APIRouter()


def require_admin(current_user: dict = Depends(AuthService.get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


@router.post("/create")
async def create_backup(
    current_user: dict = Depends(require_admin)
):
    """Manuel yedek oluştur"""
    try:
        backup_service = BackupService()
        
        # Docker container içinde 'db' hostname'i kullanılmalı
        db_host = os.getenv('DB_HOST', 'db')  # Docker compose service name
        db_port = int(os.getenv('DB_PORT', '5432'))
        db_name = os.getenv('DB_NAME', 'teknik_servis')
        db_user = os.getenv('DB_USER', 'app')  # Docker compose'da app kullanılıyor
        db_password = os.getenv('DB_PASSWORD', 'app_password')
        
        backup_path = backup_service.create_database_backup(
            db_host, db_port, db_name, db_user, db_password
        )
        
        return {
            "success": True,
            "message": "Yedek başarıyla oluşturuldu",
            "backup_path": backup_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yedek oluşturma hatası: {str(e)}"
        )


@router.get("/list")
async def list_backups(
    current_user: dict = Depends(require_admin)
):
    """Mevcut yedekleri listele"""
    try:
        backup_service = BackupService()
        backups = backup_service.list_backups()
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yedek listesi alınamadı: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    current_user: dict = Depends(require_admin)
):
    """Yedek dosyasını indir (SQL, Excel veya ZIP)"""
    try:
        # Path traversal saldırısını önle
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz dosya adı"
            )
        
        # Dosya adını normalize et
        filename = os.path.basename(filename)
        
        backup_service = BackupService()
        backup_path = backup_service.backup_dir / filename
        
        # Path traversal kontrolü (ikinci kez)
        real_path = os.path.realpath(str(backup_path))
        real_backup_dir = os.path.realpath(str(backup_service.backup_dir))
        if not real_path.startswith(real_backup_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz dosya yolu"
            )
        
        if not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Yedek dosyası bulunamadı"
            )
        
        # Dosya tipine göre media type belirle
        if filename.endswith('.xlsx'):
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.zip'):
            media_type = 'application/zip'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yedek indirme hatası: {str(e)}"
        )


@router.delete("/{filename}")
async def delete_backup(
    filename: str,
    current_user: dict = Depends(require_admin)
):
    """Yedek dosyasını sil"""
    try:
        # Path traversal saldırısını önle
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz dosya adı"
            )
        
        # Dosya adını normalize et
        filename = os.path.basename(filename)
        
        backup_service = BackupService()
        backup_service.delete_backup(filename)
        
        return {
            "success": True,
            "message": "Yedek başarıyla silindi"
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yedek silme hatası: {str(e)}"
        )


@router.post("/export-excel")
async def export_excel_backup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Tüm tabloları Excel formatında export et"""
    try:
        backup_service = BackupService()
        excel_path = backup_service.export_all_tables_to_excel(db)
        
        return {
            "success": True,
            "message": "Excel export başarıyla oluşturuldu",
            "file_path": excel_path,
            "filename": os.path.basename(excel_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel export hatası: {str(e)}"
        )


@router.get("/download-excel/{filename}")
async def download_excel_backup(
    filename: str,
    current_user: dict = Depends(require_admin)
):
    """Excel export dosyasını indir"""
    try:
        # Path traversal saldırısını önle
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz dosya adı"
            )
        
        # Dosya adını normalize et
        filename = os.path.basename(filename)
        
        backup_service = BackupService()
        excel_path = backup_service.backup_dir / filename
        
        # Path traversal kontrolü (ikinci kez)
        real_path = os.path.realpath(str(excel_path))
        real_backup_dir = os.path.realpath(str(backup_service.backup_dir))
        if not real_path.startswith(real_backup_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz dosya yolu"
            )
        
        if not excel_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Excel dosyası bulunamadı"
            )
        
        return FileResponse(
            path=str(excel_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel indirme hatası: {str(e)}"
        )


@router.post("/create-full")
async def create_full_backup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Sistemin komple yedeğini oluştur"""
    try:
        backup_service = BackupService()
        
        # Docker container içinde 'db' hostname'i kullanılmalı
        db_host = os.getenv('DB_HOST', 'db')
        db_port = int(os.getenv('DB_PORT', '5432'))
        db_name = os.getenv('DB_NAME', 'teknik_servis')
        db_user = os.getenv('DB_USER', 'app')
        db_password = os.getenv('DB_PASSWORD', 'app_password')
        
        backup_path = backup_service.create_full_system_backup(
            db, db_host, db_port, db_name, db_user, db_password
        )
        
        return {
            "success": True,
            "message": "Sistem yedeği başarıyla oluşturuldu",
            "backup_path": backup_path,
            "filename": os.path.basename(backup_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sistem yedeği oluşturma hatası: {str(e)}"
        )


@router.get("/list-all")
async def list_all_backups(
    current_user: dict = Depends(require_admin)
):
    """Tüm yedekleri listele (SQL, Excel, ZIP)"""
    try:
        backup_service = BackupService()
        
        # Tüm yedek dosyalarını listele
        all_backups = []
        
        # SQL yedekleri
        sql_backups = sorted(
            backup_service.backup_dir.glob('backup_*.sql'),
            key=os.path.getmtime,
            reverse=True
        )
        for backup in sql_backups:
            all_backups.append({
                'filename': backup.name,
                'type': 'sql',
                'size': backup.stat().st_size,
                'created_at': datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
        
        # Excel yedekleri
        excel_backups = sorted(
            backup_service.backup_dir.glob('backup_excel_*.xlsx'),
            key=os.path.getmtime,
            reverse=True
        )
        for backup in excel_backups:
            all_backups.append({
                'filename': backup.name,
                'type': 'excel',
                'size': backup.stat().st_size,
                'created_at': datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
        
        # Sistem yedekleri (ZIP)
        zip_backups = sorted(
            backup_service.backup_dir.glob('full_system_backup_*.zip'),
            key=os.path.getmtime,
            reverse=True
        )
        for backup in zip_backups:
            all_backups.append({
                'filename': backup.name,
                'type': 'full_system',
                'size': backup.stat().st_size,
                'created_at': datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
        
        # Tarihe göre sırala
        all_backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {"backups": all_backups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yedek listesi alınamadı: {str(e)}"
        )
