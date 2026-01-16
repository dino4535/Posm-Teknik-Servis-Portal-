"""
Posm Teknik İşler.xlsx dosyasından verileri PostgreSQL'e aktaran script.

Kullanım (Windows, host üzerinden):
  cd backend
  py scripts/import_from_excel.py

Docker içinden:
  docker-compose exec api python scripts/import_from_excel.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.dealer import Dealer
from app.models.territory import Territory
from app.models.posm import Posm
from app.core.security import get_password_hash


# Excel dosyasının yolu - önce data/ klasöründe, sonra backend/ klasöründe, sonra proje root'ta ara
EXCEL_FILENAME = "Posm Teknik İşler.xlsx"
# Farklı konumları dene
possible_paths = [
    os.path.join(os.path.dirname(__file__), "..", "data", EXCEL_FILENAME),  # backend/data/
    os.path.join(os.path.dirname(__file__), "..", EXCEL_FILENAME),  # backend/
    os.path.join(os.path.dirname(__file__), "..", "..", EXCEL_FILENAME),  # proje root
]

EXCEL_PATH = None
for path in possible_paths:
    if os.path.exists(path):
        EXCEL_PATH = path
        break


def safe_get(df: pd.DataFrame, row, col_name: str, default=None):
  """DataFrame'den kolonu güvenli şekilde oku."""
  if col_name not in df.columns:
    return default
  v = row.get(col_name)
  return default if pd.isna(v) else v


def import_posm(db: Session, xls: pd.ExcelFile):
  print("\n📦 POSM sheet import ediliyor...")
  # Sheet adını POSM, Posm, POSM LIST vb. olasılıklara göre bulmaya çalış
  possible_names = ["POSM", "Posm", "POSM ", "Posm Listesi", "POSM List"]
  sheet_name = None
  for name in xls.sheet_names:
    if name.strip() in possible_names:
      sheet_name = name
      break
  if sheet_name is None:
    # Son çare: ilk sheet POSM ise
    sheet_name = xls.sheet_names[0]

  df = xls.parse(sheet_name)
  print(f"   → POSM sheet: {sheet_name}")
  print(f"   → Kolonlar: {list(df.columns)}")

  # Beklenen kolon adları (Google Sheet'ten gördüğümüz)
  name_col = "Posm Adı"
  ready_col = "Hazır Adet"
  repair_col = "Tamir Bekleyen Adet"

  imported = 0
  skipped = 0

  for _, row in df.iterrows():
    posm_name = safe_get(df, row, name_col)
    if not posm_name:
      continue

    ready_val = safe_get(df, row, ready_col, 0)
    repair_val = safe_get(df, row, repair_col, 0)
    try:
      ready = int(ready_val) if ready_val not in (None, "") else 0
    except Exception:
      ready = 0
    try:
      repair = int(repair_val) if repair_val not in (None, "") else 0
    except Exception:
      repair = 0

    existing = db.query(Posm).filter(Posm.name == posm_name).first()
    if existing:
      existing.ready_count = ready
      existing.repair_pending_count = repair
      skipped += 1
    else:
      db.add(
        Posm(
          name=posm_name,
          ready_count=ready,
          repair_pending_count=repair,
        )
      )
      imported += 1

  db.commit()
  print(f"✅ POSM: {imported} yeni, {skipped} güncelleme/skip")


def import_dealers_and_territories(db: Session, xls: pd.ExcelFile):
  print("\n🏪 Bayiler sheet import ediliyor...")
  # Sheet adını bul (Bayiler, Dealer, Bayi Listesi vs.)
  possible_names = ["Bayiler", "Bayi", "Dealer", "Bayiler ", "Bayiler Listesi"]
  sheet_name = None
  for name in xls.sheet_names:
    if name.strip() in possible_names:
      sheet_name = name
      break
  if sheet_name is None:
    print("⚠️  Bayiler için ayrı sheet bulunamadı (Bu adımı atlıyorum)")
    return

  df = xls.parse(sheet_name)
  print(f"   → Bayiler sheet: {sheet_name}")
  print(f"   → Kolonlar: {list(df.columns)}")

  # Burada kolon isimlerini senin Excel'ine göre uyarlıyoruz.
  # Örnek varsayımlar (gerekirse isimleri sen bana söyle, güncelleriz):
  territory_col = "Territory"
  code_col = "Bayi Kodu"
  name_col = "Bayi Adı"
  lat_col = "Latitude"
  lon_col = "Longitude"

  imported = 0
  skipped = 0
  errors = 0

  # Önce tüm territory'leri topla ve oluştur
  territory_map = {}
  for _, row in df.iterrows():
    territory_name = safe_get(df, row, territory_col)
    if territory_name and territory_name not in territory_map:
      terr = db.query(Territory).filter(Territory.name == territory_name).first()
      if not terr:
        terr = Territory(name=territory_name)
        db.add(terr)
        db.commit()
        db.refresh(terr)
      territory_map[territory_name] = terr.id

  # Şimdi bayileri tek tek işle (duplicate kontrolü için)
  for _, row in df.iterrows():
    code = safe_get(df, row, code_col)
    name = safe_get(df, row, name_col)
    if not code or not name:
      skipped += 1
      continue

    territory_name = safe_get(df, row, territory_col)
    territory_id = territory_map.get(territory_name) if territory_name else None

    lat = safe_get(df, row, lat_col)
    lon = safe_get(df, row, lon_col)
    try:
      lat_val = float(str(lat).replace(",", ".")) if lat not in (None, "") else None
    except Exception:
      lat_val = None
    try:
      lon_val = float(str(lon).replace(",", ".")) if lon not in (None, "") else None
    except Exception:
      lon_val = None

    # Her satır için duplicate kontrolü yap
    try:
      existing = db.query(Dealer).filter(Dealer.code == code).first()
      if existing:
        # Mevcut kaydı güncelle
        existing.name = name
        existing.territory_id = territory_id
        existing.latitude = lat_val
        existing.longitude = lon_val
        db.commit()
        skipped += 1
      else:
        # Yeni kayıt ekle
        dealer = Dealer(
          code=code,
          name=name,
          territory_id=territory_id,
          latitude=lat_val,
          longitude=lon_val,
        )
        db.add(dealer)
        db.commit()
        imported += 1
    except Exception as e:
      errors += 1
      db.rollback()
      print(f"  ⚠️  Bayi hatası (kod: {code}): {str(e)[:100]}")
      continue

  print(f"✅ Bayiler: {imported} yeni, {skipped} güncelleme/skip, {errors} hata")


def import_users(db: Session, xls: pd.ExcelFile):
  print("\n👥 User sheet import ediliyor...")
  possible_names = ["User", "Users", "Kullanıcılar"]
  sheet_name = None
  for name in xls.sheet_names:
    if name.strip() in possible_names:
      sheet_name = name
      break
  if sheet_name is None:
    print("⚠️  User sheet bulunamadı (Bu adımı atlıyorum)")
    return

  df = xls.parse(sheet_name)
  print(f"   → User sheet: {sheet_name}")
  print(f"   → Kolonlar: {list(df.columns)}")

  # Kolon isimlerini Excel'deki gerçek isimlere göre ayarla
  # Excel'de: ['Depo', 'İsim Soyisim', 'E-Mail', 'Şifre', 'Rol']
  name_col = "İsim Soyisim" if "İsim Soyisim" in df.columns else "Name"
  email_col = "E-Mail" if "E-Mail" in df.columns else "Email"
  role_col = "Rol" if "Rol" in df.columns else "Role"
  password_col = "Şifre" if "Şifre" in df.columns else "Password"

  imported = 0
  skipped = 0
  errors = 0

  for _, row in df.iterrows():
    name = safe_get(df, row, name_col)
    email = safe_get(df, row, email_col)
    if not name or not email:
      skipped += 1
      continue

    role_str = str(safe_get(df, row, role_col, "user")).lower().strip()
    password = safe_get(df, row, password_col)

    # Role'ü belirle
    if role_str in ("admin", "administrator", "yönetici"):
      role = UserRole.ADMIN.value
    elif role_str in ("tech", "technical", "teknik", "teknik sorumlu"):
      role = UserRole.TECH.value
    else:
      role = UserRole.USER.value

    # Her kullanıcıyı tek tek işle (duplicate kontrolü için)
    try:
      existing = db.query(User).filter(User.email == email).first()
      if existing:
        existing.name = name
        existing.role = role
        if password:
          existing.password_hash = get_password_hash(password)
        db.commit()
        skipped += 1
      else:
        default_password = password if password else "Password123!"
        user = User(
          name=name,
          email=email,
          password_hash=get_password_hash(default_password),
          role=role,
        )
        db.add(user)
        db.commit()
        imported += 1
        if not password:
          print(f"  ⚠️  {email} için varsayılan şifre: Password123!")
    except Exception as e:
      errors += 1
      db.rollback()
      print(f"  ⚠️  Kullanıcı hatası (email: {email}): {str(e)[:100]}")
      continue

  print(f"✅ Kullanıcılar: {imported} yeni, {skipped} güncelleme/skip, {errors} hata")


def main():
  print("🚀 Excel'den veri import başlıyor...\n")

  if EXCEL_PATH is None or not os.path.exists(EXCEL_PATH):
    print(f"❌ Excel dosyası bulunamadı: {EXCEL_FILENAME}")
    print("\n📁 Dosyayı şu konumlardan birine koy:")
    for path in possible_paths:
      print(f"   - {path}")
    print(f"\n   Veya dosyayı şuraya kopyala: backend/data/{EXCEL_FILENAME}")
    return

  print(f"📁 Excel dosyası: {EXCEL_PATH}")

  # Excel'i aç
  xls = pd.ExcelFile(EXCEL_PATH)
  print(f"   → Sheet'ler: {xls.sheet_names}\n")

  db = SessionLocal()

  try:
    import_posm(db, xls)
    import_dealers_and_territories(db, xls)
    import_users(db, xls)
    print("\n✅ Excel import işlemi tamamlandı!")
  except Exception as e:
    import traceback

    print(f"\n❌ Import hatası: {e}")
    traceback.print_exc()
    db.rollback()
  finally:
    db.close()


if __name__ == "__main__":
  main()

