# 🚀 Hızlı Başlangıç Kılavuzu

## 1. Backend'i Başlat

```bash
# Docker servislerini başlat
docker-compose up -d db api

# Migration'ları kontrol et (zaten çalıştırıldı)
docker-compose exec api alembic current

# API loglarını izle
docker-compose logs -f api
```

Backend hazır! → `http://localhost:8000/docs`

## 2. Frontend'i Başlat

```bash
cd frontend
npm install
npm run dev
```

Frontend hazır! → `http://localhost:5173`

## 3. İlk Giriş

- **URL**: http://localhost:5173
- **Email**: admin@example.com
- **Şifre**: Admin123!

## 4. Test Senaryoları

### Senaryo 1: Yeni Talep Oluştur
1. "Yeni Talep" menüsüne git
2. Territory seç
3. Bayi ara ve seç
4. Yapılacak iş seç (Montaj/Demontaj/Bakım)
5. POSM seç (Montaj/Demontaj için)
6. Fotoğraf yükle (opsiyonel)
7. "Talep Oluştur" butonuna tıkla

### Senaryo 2: Talepleri Görüntüle
1. "Taleplerim" menüsüne git
2. Tablo görünümünde talepleri gör
3. "Takvim Görünümü" butonuna tıkla
4. Takvimde bir olaya tıkla → Detay modal açılır

### Senaryo 3: Talep Güncelle (Admin)
1. "Tüm Talepler" menüsüne git (admin only)
2. Bir talebe "Detay" butonuna tıkla
3. Modal'da durum, planlanan tarih, yapılan işler güncelle
4. "Güncelle" butonuna tıkla

### Senaryo 4: POSM Yönetimi (Admin)
1. "POSM Yönetimi" menüsüne git
2. POSM listesini gör
3. "Düzenle" butonuna tıkla
4. Stok bilgilerini güncelle
5. "Kaydet" butonuna tıkla

## 🔍 Sorun Giderme

### Backend çalışmıyor
```bash
docker-compose logs api
docker-compose ps
```

### Frontend çalışmıyor
```bash
cd frontend
npm install  # Bağımlılıkları tekrar yükle
npm run dev
```

### API istekleri başarısız
- Backend'in çalıştığını kontrol et: `http://localhost:8000/health`
- Browser console'da hata mesajlarını kontrol et
- Network tab'ında API isteklerini kontrol et

### Login başarısız
- Admin kullanıcının var olduğunu kontrol et:
```bash
docker-compose exec db psql -U app -d teknik_servis -c "SELECT email, role FROM users;"
```

## 📊 Veritabanı Komutları

```bash
# PostgreSQL'e bağlan
docker-compose exec db psql -U app -d teknik_servis

# Tabloları listele
\dt

# Users tablosunu görüntüle
SELECT * FROM users;

# Requests tablosunu görüntüle
SELECT * FROM requests;
```

## 🎯 Sonraki Adımlar

1. **Veri Migrasyonu**: Google Sheets'ten mevcut verileri PostgreSQL'e aktar
2. **Test Verileri**: Örnek territory, dealer, POSM verileri ekle
3. **Production Deployment**: Sunucuya deploy et
