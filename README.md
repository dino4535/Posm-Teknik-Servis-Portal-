# Teknik Servis Portalı

Modern stack'e taşınmış Teknik Servis ve POSM Yönetim Sistemi.

## 🚀 Teknoloji Stack'i

- **Backend**: Python 3.11 + FastAPI
- **Database**: PostgreSQL 16
- **Frontend**: React 18 + Vite
- **Containerization**: Docker + Docker Compose

## 📋 Kurulum

### 1. Environment Variables

`.env.example` dosyasını kopyalayıp `.env` oluşturun:

```bash
cp .env.example .env
```

`.env` dosyasında gerekli değerleri düzenleyin (özellikle `SECRET_KEY`).

### 2. Docker ile Çalıştırma

```bash
# Tüm servisleri başlat
docker-compose up -d

# Migration'ları çalıştır
docker-compose exec api alembic upgrade head

# Logları izle
docker-compose logs -f
```

### 3. Lokal Geliştirme

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

- `POST /auth/login` - Kullanıcı girişi
- `GET /auth/me` - Mevcut kullanıcı bilgisi
- `GET /requests` - Talepleri listele
- `POST /requests` - Yeni talep oluştur
- `GET /posm` - POSM listesi
- `GET /dealers` - Bayi arama

Detaylı API dokümantasyonu: `http://localhost:8000/docs`

## 📝 Migration Plan

Detaylı geçiş planı için `MIGRATION_PLAN.md` dosyasına bakın.

## 🔐 Güvenlik

- JWT tabanlı authentication
- Password hashing (bcrypt)
- Role-based authorization
- Input validation (Pydantic)

## 📦 Proje Yapısı

```
Proje1/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── docker-compose.yml
└── .env.example
```
