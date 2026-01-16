# Veri Import Kılavuzu

Google Sheets'ten verileri PostgreSQL'e aktarmak için iki yöntem var:

## Yöntem 1: CSV Export (Önerilen - Daha Kolay)

### Adımlar:

1. **Google Sheets'ten CSV Export Al:**
   - Google Sheets'i aç: https://docs.google.com/spreadsheets/d/1hJwn0iRV9Ma3Iu_dn-9nHO0wmoPUqJcYkFIi9H4hE00
   - Her sayfayı ayrı ayrı CSV olarak export et:
     - **User** sayfası → `File` > `Download` > `Comma Separated Values (.csv)` → `User.csv`
     - **Bayiler** sayfası → `File` > `Download` > `Comma Separated Values (.csv)` → `Bayiler.csv`
     - **POSM** sayfası → `File` > `Download` > `Comma Separated Values (.csv)` > `POSM.csv`

2. **CSV Dosyalarını Kopyala:**
   - CSV dosyalarını `backend/data/` klasörüne koy

3. **Script'i Çalıştır:**
   ```bash
   cd backend
   docker-compose exec api python scripts/import_from_csv.py
   ```
   
   Veya lokal Python ile:
   ```bash
   cd backend
   python scripts/import_from_csv.py
   ```

## Yöntem 2: Google Sheets API (Daha Gelişmiş)

### Adımlar:

1. **Google Cloud Console Setup:**
   - Detaylı kurulum için: `backend/scripts/GOOGLE_SHEETS_SETUP.md` dosyasına bak

2. **Script'i Çalıştır:**
   ```bash
   cd backend
   docker-compose exec api python scripts/import_from_sheets.py
   ```

## CSV Formatı

### User.csv
```
Name,Email,Role,Password
Ahmet Yılmaz,ahmet@example.com,user,Password123!
Mehmet Admin,admin@example.com,admin,Admin123!
```

### Bayiler.csv
```
Territory,Bayi Kodu,Bayi Adı,Latitude,Longitude
Manisa,BAYI001,Manisa Merkez,38.6191,27.4289
İzmir,BAYI002,İzmir Bornova,38.4622,27.2208
```

### POSM.csv
```
Posm Adı,Hazır Adet,Tamir Bekleyen Adet
POS'a Ait Ünite,10,5
Multiplex,5,2
100X35 ATLAS,10,5
```

## Notlar

- Mevcut kayıtlar güncellenir (email/code bazında)
- Yeni kayıtlar eklenir
- Territory'ler Bayiler sayfasından otomatik çıkarılır
- Şifre belirtilmezse varsayılan: `Password123!`
