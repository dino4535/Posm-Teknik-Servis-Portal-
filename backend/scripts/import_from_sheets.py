"""
Google Sheets'ten veri çekip PostgreSQL'e aktaran script
Kullanım:
1. Google Sheets API credentials oluştur (service account)
2. credentials.json dosyasını backend/ klasörüne koy
3. Script'i çalıştır: python scripts/import_from_sheets.py
"""

import os
import sys
from pathlib import Path

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.dealer import Dealer
from app.models.territory import Territory
from app.models.posm import Posm
from app.core.security import get_password_hash
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets ID
SHEET_ID = "1hJwn0iRV9Ma3Iu_dn-9nHO0wmoPUqJcYkFIi9H4hE00"

# Credentials dosyası yolu
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials.json")


def get_sheets_client():
    """Google Sheets client'ı oluştur"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except FileNotFoundError:
        print(f"❌ credentials.json dosyası bulunamadı: {CREDENTIALS_PATH}")
        print("📝 Google Cloud Console'dan service account credentials oluşturup buraya koymalısın.")
        return None
    except Exception as e:
        print(f"❌ Google Sheets bağlantı hatası: {e}")
        return None


def import_territories(db: Session, sheet):
    """Territory verilerini import et"""
    print("\n📍 Territory'leri import ediliyor...")
    try:
        # Territory sayfasını bul (eğer varsa)
        # Şimdilik manuel olarak ekleyeceğiz veya Bayiler sayfasından çıkaracağız
        print("⚠️  Territory sayfası bulunamadı, Bayiler sayfasından çıkarılacak")
        return {}
    except Exception as e:
        print(f"❌ Territory import hatası: {e}")
        return {}


def import_dealers(db: Session, sheet, territories_map):
    """Bayiler verilerini import et"""
    print("\n🏪 Bayiler import ediliyor...")
    try:
        dealers_sheet = sheet.worksheet("Bayiler")
        dealers_data = dealers_sheet.get_all_values()
        
        if len(dealers_data) < 2:
            print("⚠️  Bayiler sayfası boş veya sadece başlık var")
            return
        
        # Başlık satırını atla
        headers = dealers_data[0]
        print(f"📋 Başlıklar: {headers}")
        
        imported = 0
        skipped = 0
        
        for row in dealers_data[1:]:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
                # Sütun yapısını anlamak için başlıklara bak
                # Genellikle: Territory, Bayi Kodu, Bayi Adı, vb.
                territory_name = row[0].strip() if len(row) > 0 else None
                dealer_code = row[1].strip() if len(row) > 1 else None
                dealer_name = row[2].strip() if len(row) > 2 else None
                latitude = row[3] if len(row) > 3 and row[3] else None
                longitude = row[4] if len(row) > 4 and row[4] else None
                
                if not dealer_code or not dealer_name:
                    skipped += 1
                    continue
                
                # Territory'yi bul veya oluştur
                territory_id = None
                if territory_name:
                    territory = db.query(Territory).filter(Territory.name == territory_name).first()
                    if not territory:
                        territory = Territory(name=territory_name)
                        db.add(territory)
                        db.commit()
                        db.refresh(territory)
                    territory_id = territory.id
                
                # Dealer'ı kontrol et
                existing = db.query(Dealer).filter(Dealer.code == dealer_code).first()
                if existing:
                    # Güncelle
                    existing.name = dealer_name
                    existing.territory_id = territory_id
                    if latitude:
                        try:
                            existing.latitude = float(latitude.replace(',', '.'))
                        except:
                            pass
                    if longitude:
                        try:
                            existing.longitude = float(longitude.replace(',', '.'))
                        except:
                            pass
                    skipped += 1
                else:
                    # Yeni dealer oluştur
                    dealer = Dealer(
                        code=dealer_code,
                        name=dealer_name,
                        territory_id=territory_id,
                        latitude=float(latitude.replace(',', '.')) if latitude else None,
                        longitude=float(longitude.replace(',', '.')) if longitude else None
                    )
                    db.add(dealer)
                    imported += 1
                
            except Exception as e:
                print(f"⚠️  Satır hatası: {row} - {e}")
                skipped += 1
                continue
        
        db.commit()
        print(f"✅ {imported} bayi eklendi, {skipped} atlandı/güncellendi")
        
    except gspread.exceptions.WorksheetNotFound:
        print("❌ 'Bayiler' sayfası bulunamadı")
    except Exception as e:
        print(f"❌ Bayiler import hatası: {e}")
        db.rollback()


def import_users(db: Session, sheet):
    """Kullanıcı verilerini import et"""
    print("\n👥 Kullanıcılar import ediliyor...")
    try:
        users_sheet = sheet.worksheet("User")
        users_data = users_sheet.get_all_values()
        
        if len(users_data) < 2:
            print("⚠️  User sayfası boş veya sadece başlık var")
            return
        
        headers = users_data[0]
        print(f"📋 Başlıklar: {headers}")
        
        imported = 0
        skipped = 0
        
        for row in users_data[1:]:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
                # Sütun yapısı: Name, Email, Role, Password (opsiyonel)
                name = row[0].strip() if len(row) > 0 else None
                email = row[1].strip() if len(row) > 1 else None
                role_str = row[2].strip().lower() if len(row) > 2 else "user"
                password = row[3] if len(row) > 3 and row[3] else None
                
                if not name or not email:
                    skipped += 1
                    continue
                
                # Role'ü belirle
                if role_str in ["admin", "administrator"]:
                    role = UserRole.ADMIN.value
                elif role_str in ["tech", "technical", "teknik"]:
                    role = UserRole.TECH.value
                else:
                    role = UserRole.USER.value
                
                # Kullanıcıyı kontrol et
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    # Güncelle
                    existing.name = name
                    existing.role = role
                    if password:
                        existing.password_hash = get_password_hash(password)
                    skipped += 1
                else:
                    # Yeni kullanıcı oluştur
                    # Şifre yoksa varsayılan şifre kullan
                    default_password = password if password else "Password123!"
                    user = User(
                        name=name,
                        email=email,
                        password_hash=get_password_hash(default_password),
                        role=role
                    )
                    db.add(user)
                    imported += 1
                    if not password:
                        print(f"  ⚠️  {email} için varsayılan şifre kullanıldı: Password123!")
                
            except Exception as e:
                print(f"⚠️  Satır hatası: {row} - {e}")
                skipped += 1
                continue
        
        db.commit()
        print(f"✅ {imported} kullanıcı eklendi, {skipped} atlandı/güncellendi")
        
    except gspread.exceptions.WorksheetNotFound:
        print("❌ 'User' sayfası bulunamadı")
    except Exception as e:
        print(f"❌ Kullanıcı import hatası: {e}")
        db.rollback()


def import_posm(db: Session, sheet):
    """POSM verilerini import et"""
    print("\n📦 POSM verileri import ediliyor...")
    try:
        posm_sheet = sheet.worksheet("POSM")
        posm_data = posm_sheet.get_all_values()
        
        if len(posm_data) < 2:
            print("⚠️  POSM sayfası boş veya sadece başlık var")
            return
        
        headers = posm_data[0]
        print(f"📋 Başlıklar: {headers}")
        
        imported = 0
        skipped = 0
        
        for row in posm_data[1:]:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
                # Sütun yapısı: Posm Adı, Hazır Adet, Tamir Bekleyen Adet
                posm_name = row[0].strip() if len(row) > 0 else None
                ready_count = row[1] if len(row) > 1 and row[1] else "0"
                repair_count = row[2] if len(row) > 2 and row[2] else "0"
                
                if not posm_name:
                    skipped += 1
                    continue
                
                # Sayıları parse et
                try:
                    ready = int(ready_count) if ready_count else 0
                    repair = int(repair_count) if repair_count else 0
                except:
                    ready = 0
                    repair = 0
                
                # POSM'ı kontrol et
                existing = db.query(Posm).filter(Posm.name == posm_name).first()
                if existing:
                    # Güncelle
                    existing.ready_count = ready
                    existing.repair_pending_count = repair
                    skipped += 1
                else:
                    # Yeni POSM oluştur
                    posm = Posm(
                        name=posm_name,
                        ready_count=ready,
                        repair_pending_count=repair
                    )
                    db.add(posm)
                    imported += 1
                
            except Exception as e:
                print(f"⚠️  Satır hatası: {row} - {e}")
                skipped += 1
                continue
        
        db.commit()
        print(f"✅ {imported} POSM eklendi, {skipped} atlandı/güncellendi")
        
    except gspread.exceptions.WorksheetNotFound:
        print("❌ 'POSM' sayfası bulunamadı")
    except Exception as e:
        print(f"❌ POSM import hatası: {e}")
        db.rollback()


def main():
    """Ana import fonksiyonu"""
    print("🚀 Google Sheets'ten veri import başlıyor...\n")
    
    # Google Sheets client
    client = get_sheets_client()
    if not client:
        return
    
    # Spreadsheet'i aç
    try:
        sheet = client.open_by_key(SHEET_ID)
        print(f"✅ Google Sheets bağlantısı başarılı: {sheet.title}\n")
    except Exception as e:
        print(f"❌ Spreadsheet açılamadı: {e}")
        return
    
    # Database bağlantısı
    db = SessionLocal()
    
    try:
        # Territory'leri import et (Bayiler'den çıkarılacak)
        territories_map = import_territories(db, sheet)
        
        # Bayiler'i import et
        import_dealers(db, sheet, territories_map)
        
        # Kullanıcıları import et
        import_users(db, sheet)
        
        # POSM'ları import et
        import_posm(db, sheet)
        
        print("\n✅ Import işlemi tamamlandı!")
        
    except Exception as e:
        print(f"\n❌ Import hatası: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
