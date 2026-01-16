"""
İlk admin kullanıcıyı oluşturur.
Kullanım: python scripts/create_admin.py
"""
import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin_user():
    """İlk admin kullanıcıyı oluştur"""
    db: Session = SessionLocal()
    
    try:
        # Admin kullanıcı zaten var mı kontrol et
        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print("Admin kullanıcı zaten mevcut!")
            return
        
        # Yeni admin kullanıcı oluştur
        password = "Admin123!"
        # Enum value'sunu direkt string olarak kullan (native_enum=False olduğu için)
        admin_user = User(
            name="Admin Kullanıcı",
            email="admin@example.com",
            password_hash=get_password_hash(password),
            role="admin"  # Direkt string olarak gönder
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin kullanıcı başarıyla oluşturuldu!")
        print("   Email: admin@example.com")
        print("   Şifre: Admin123!")
        print("   ⚠️  İlk girişten sonra şifreyi değiştirmeyi unutmayın!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Hata: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
