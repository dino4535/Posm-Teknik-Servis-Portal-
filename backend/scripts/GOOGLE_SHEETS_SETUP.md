# Google Sheets API Kurulumu

## 1. Google Cloud Console'da Service Account Oluştur

1. [Google Cloud Console](https://console.cloud.google.com/)'a git
2. Yeni bir proje oluştur veya mevcut projeyi seç
3. **APIs & Services** > **Library**'ye git
4. **Google Sheets API** ve **Google Drive API**'yi etkinleştir
5. **APIs & Services** > **Credentials**'a git
6. **Create Credentials** > **Service Account** seç
7. Service account adı ver (örn: "sheets-importer")
8. **Create and Continue** > **Done**

## 2. Service Account Key İndir

1. Oluşturduğun service account'a tıkla
2. **Keys** sekmesine git
3. **Add Key** > **Create new key**
4. **JSON** formatını seç ve indir
5. İndirilen JSON dosyasını `backend/credentials.json` olarak kaydet

## 3. Google Sheets'i Paylaş

1. Google Sheets'i aç: https://docs.google.com/spreadsheets/d/1hJwn0iRV9Ma3Iu_dn-9nHO0wmoPUqJcYkFIi9H4hE00
2. **Share** butonuna tıkla
3. Service account'un email adresini bul (credentials.json içinde `client_email` alanında)
4. Bu email'i **Viewer** yetkisiyle ekle

## 4. Script'i Çalıştır

```bash
cd backend
python scripts/import_from_sheets.py
```

## Alternatif: CSV Export (Daha Kolay)

Eğer Google Sheets API kurulumu zor geliyorsa:

1. Google Sheets'te her sayfayı CSV olarak export et:
   - **File** > **Download** > **Comma Separated Values (.csv)**
2. CSV dosyalarını `backend/data/` klasörüne koy
3. `import_from_csv.py` scriptini kullan (yakında eklenecek)
