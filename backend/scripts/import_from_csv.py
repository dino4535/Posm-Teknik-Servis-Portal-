"""
CSV dosyalarından veri çekip PostgreSQL'e aktaran script
Kullanım:
1. Google Sheets'ten CSV export al (User, Bayiler, POSM sayfaları)
2. CSV dosyalarını backend/data/ klasörüne koy
3. Script'i çalıştır: python scripts/import_from_csv.py
"""

import os
import sys
import csv
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

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def import_territories_from_dealers(db: Session, dealers_file):
    """Bayiler CSV'sinden territory'leri çıkar"""
    territories_map = {}
    if not os.path.exists(dealers_file):
        return territories_map
    
    with open(dealers_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Başlık satırını atla
        
        for row in reader:
            if len(row) > 0 and row[0].strip():
                territory_name = row[0].strip()
                if territory_name and territory_name not in territories_map:
                    territory = db.query(Territory).filter(Territory.name == territory_name).first()
                    if not territory:
                        territory = Territory(name=territory_name)
                        db.add(territory)
                        db.commit()
                        db.refresh(territory)
                    territories_map[territory_name] = territory.id
    
    return territories_map


def import_dealers_from_csv(db: Session, territories_map):
    """Bayiler CSV'sini import et"""
    dealers_file = os.path.join(DATA_DIR, "Bayiler.csv")
    
    if not os.path.exists(dealers_file):
        print("⚠️  Bayiler.csv bulunamadı")
        return
    
    print("\n🏪 Bayiler import ediliyor...")
    
    imported = 0
    skipped = 0
    
    with open(dealers_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print(f"📋 Başlıklar: {headers}")
        
        for row in reader:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
                territory_name = row[0].strip() if len(row) > 0 else None
                dealer_code = row[1].strip() if len(row) > 1 else None
                dealer_name = row[2].strip() if len(row) > 2 else None
                latitude = row[3] if len(row) > 3 and row[3] else None
                longitude = row[4] if len(row) > 4 and row[4] else None
                
                if not dealer_code or not dealer_name:
                    skipped += 1
                    continue
                
                # Territory ID'yi bul
                territory_id = territories_map.get(territory_name) if territory_name else None
                
                # Dealer'ı kontrol et
                existing = db.query(Dealer).filter(Dealer.code == dealer_code).first()
                if existing:
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


def import_users_from_csv(db: Session):
    """Kullanıcılar CSV'sini import et"""
    users_file = os.path.join(DATA_DIR, "User.csv")
    
    if not os.path.exists(users_file):
        print("⚠️  User.csv bulunamadı")
        return
    
    print("\n👥 Kullanıcılar import ediliyor...")
    
    imported = 0
    skipped = 0
    
    with open(users_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print(f"📋 Başlıklar: {headers}")
        
        for row in reader:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
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
                    existing.name = name
                    existing.role = role
                    if password:
                        existing.password_hash = get_password_hash(password)
                    skipped += 1
                else:
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
                        print(f"  ⚠️  {email} için varsayılan şifre: Password123!")
                
            except Exception as e:
                print(f"⚠️  Satır hatası: {row} - {e}")
                skipped += 1
                continue
    
    db.commit()
    print(f"✅ {imported} kullanıcı eklendi, {skipped} atlandı/güncellendi")


def import_posm_from_csv(db: Session):
    """POSM CSV'sini import et"""
    posm_file = os.path.join(DATA_DIR, "POSM.csv")
    
    if not os.path.exists(posm_file):
        print("⚠️  POSM.csv bulunamadı")
        return
    
    print("\n📦 POSM verileri import ediliyor...")
    
    imported = 0
    skipped = 0
    
    with open(posm_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print(f"📋 Başlıklar: {headers}")
        
        for row in reader:
            if not row or not row[0]:  # Boş satırları atla
                continue
            
            try:
                posm_name = row[0].strip() if len(row) > 0 else None
                ready_count = row[1] if len(row) > 1 and row[1] else "0"
                repair_count = row[2] if len(row) > 2 and row[2] else "0"
                
                if not posm_name:
                    skipped += 1
                    continue
                
                try:
                    ready = int(ready_count) if ready_count else 0
                    repair = int(repair_count) if repair_count else 0
                except:
                    ready = 0
                    repair = 0
                
                # POSM'ı kontrol et
                existing = db.query(Posm).filter(Posm.name == posm_name).first()
                if existing:
                    existing.ready_count = ready
                    existing.repair_pending_count = repair
                    skipped += 1
                else:
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


def main():
    """Ana import fonksiyonu"""
    print("🚀 CSV dosyalarından veri import başlıyor...\n")
    
    # Data klasörünü kontrol et
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 {DATA_DIR} klasörü oluşturuldu")
        print("📝 Lütfen CSV dosyalarını bu klasöre koy:")
        print("   - User.csv")
        print("   - Bayiler.csv")
        print("   - POSM.csv")
        return
    
    # Database bağlantısı
    db = SessionLocal()
    
    try:
        # Önce Bayiler'den territory'leri çıkar
        dealers_file = os.path.join(DATA_DIR, "Bayiler.csv")
        territories_map = import_territories_from_dealers(db, dealers_file)
        
        # Bayiler'i import et
        import_dealers_from_csv(db, territories_map)
        
        # Kullanıcıları import et
        import_users_from_csv(db)
        
        # POSM'ları import et
        import_posm_from_csv(db)
        
        print("\n✅ Import işlemi tamamlandı!")
        
    except Exception as e:
        print(f"\n❌ Import hatası: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
