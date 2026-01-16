# Teknik Servis Portalı - Apps Script'ten Modern Stack'e Geçiş Planı

## 📋 Genel Bakış

Bu proje, Google Apps Script üzerinde çalışan bir Teknik Servis Portalı'nı modern bir stack'e (FastAPI + React + PostgreSQL + Docker) taşıyor.

## 🎯 Teknoloji Stack'i

### Backend
- **Framework**: Python 3.11+ + FastAPI
- **ORM**: SQLAlchemy 2.0
- **Migration**: Alembic
- **Database**: PostgreSQL 16
- **Auth**: JWT (access + refresh tokens)
- **File Storage**: Lokal `uploads/` klasörü (Docker volume)

### Frontend
- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Calendar**: FullCalendar (React wrapper)
- **UI**: Mevcut HTML/CSS tasarımının React component'lere port edilmesi

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Services**: 
  - `db`: PostgreSQL
  - `api`: FastAPI backend
  - `frontend`: React build (Nginx serve)

## 📁 Proje Yapısı

```
Proje1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI uygulaması
│   │   ├── core/
│   │   │   ├── config.py           # Ayarlar (.env'den)
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   └── dependencies.py     # Auth dependencies
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── dealer.py
│   │   │   ├── posm.py
│   │   │   ├── request.py
│   │   │   ├── photo.py
│   │   │   └── territory.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── request.py
│   │   │   ├── posm.py
│   │   │   └── dealer.py
│   │   ├── api/
│   │   │   ├── routes_auth.py
│   │   │   ├── routes_requests.py
│   │   │   ├── routes_posm.py
│   │   │   ├── routes_dealers.py
│   │   │   └── routes_photos.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── request_service.py
│   │   │   └── posm_service.py
│   │   └── db/
│   │       ├── base.py
│   │       ├── session.py
│   │       └── base_class.py
│   ├── alembic/
│   │   └── versions/               # Migration dosyaları
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── NewRequestPage.jsx
│   │   │   ├── MyRequestsPage.jsx
│   │   │   ├── AllRequestsPage.jsx
│   │   │   └── PosmManagementPage.jsx
│   │   ├── components/
│   │   │   ├── DashboardLayout.jsx
│   │   │   ├── RequestTable.jsx
│   │   │   ├── RequestCalendar.jsx
│   │   │   └── PhotoUpload.jsx
│   │   ├── api/
│   │   │   └── client.js           # Axios instance
│   │   ├── utils/
│   │   │   └── auth.js             # Token yönetimi
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🗄️ Veritabanı Şeması

### users
- `id` (PK, serial)
- `name` (varchar)
- `email` (varchar, unique)
- `password_hash` (varchar)
- `role` (enum: 'user', 'admin', 'tech')
- `created_at` (timestamp)
- `updated_at` (timestamp)

### territories
- `id` (PK, serial)
- `name` (varchar, unique)

### dealers (Bayiler)
- `id` (PK, serial)
- `territory_id` (FK → territories.id)
- `code` (varchar, unique)
- `name` (varchar)
- `latitude` (decimal)
- `longitude` (decimal)

### posm
- `id` (PK, serial)
- `name` (varchar, unique)
- `ready_count` (integer, default 0)
- `repair_pending_count` (integer, default 0)
- `created_at` (timestamp)
- `updated_at` (timestamp)

### requests (Teknik İşler)
- `id` (PK, serial)
- `user_id` (FK → users.id)
- `dealer_id` (FK → dealers.id)
- `territory_id` (FK → territories.id, nullable)
- `current_posm` (varchar, nullable)
- `job_type` (enum: 'Montaj', 'Demontaj', 'Bakım')
- `job_detail` (text)
- `request_date` (timestamp)
- `requested_date` (date)
- `planned_date` (date, nullable)
- `posm_id` (FK → posm.id, nullable)
- `status` (enum: 'Beklemede', 'TakvimeEklendi', 'Tamamlandı', 'İptal')
- `job_done_desc` (text, nullable)
- `latitude` (decimal, nullable)
- `longitude` (decimal, nullable)
- `updated_at` (timestamp)
- `updated_by` (FK → users.id, nullable)

### photos
- `id` (PK, serial)
- `request_id` (FK → requests.id)
- `path_or_url` (varchar)
- `file_name` (varchar)
- `mime_type` (varchar)
- `created_at` (timestamp)

## 🔄 Apps Script Fonksiyonları → API Endpoint'leri Mapping

| Apps Script Fonksiyonu | HTTP Endpoint | Method |
|------------------------|---------------|--------|
| `validateLogin(email, password)` | `/auth/login` | POST |
| `getUserRequests(email)` | `/requests?mine=true` | GET |
| `getAllRequests()` | `/requests` | GET (admin) |
| `getRequestCounts(email)` | `/requests/stats` | GET |
| `getRequestDetails(requestId)` | `/requests/{id}` | GET |
| `createServiceRequest(formData)` | `/requests` | POST |
| `updateRequestStatusAdmin(...)` | `/requests/{id}` | PATCH |
| `updatePlannedDate(...)` | `/requests/{id}` | PATCH |
| `getPosmList()` | `/posm` | GET |
| `getPosmDetails(posmName)` | `/posm/{id}` | GET |
| `updatePosmStockAdmin(...)` | `/posm/{id}` | PATCH |
| `updatePosmItem(...)` | `/posm/{id}` | PATCH |
| `deletePosmItem(posmName)` | `/posm/{id}` | DELETE |
| `getTerritoryList()` | `/territories` | GET |
| `searchBayiler(territory, searchTerm)` | `/dealers?territory=&search=` | GET |
| `getBayiInfo(bayiKodu)` | `/dealers/{code}` | GET |
| `uploadPhotos(photoData, requestId)` | `/requests/{id}/photos` | POST |

## 📝 Uygulama Adımları (Todo List)

### Faz 1: Backend İskeleti (1-4)
1. ✅ Proje klasör yapısını oluştur
2. ⏳ Backend iskeleti: FastAPI projesi, main.py, config, database bağlantısı
3. ⏳ Database modelleri: SQLAlchemy modelleri
4. ⏳ Alembic migration sistemi kurulumu ve ilk migration

### Faz 2: Auth Sistemi (5-6)
5. ⏳ Auth sistemi: JWT token, password hashing, login endpoint, role-based permissions
6. ⏳ API Routes: Auth endpoints (login, me, refresh)

### Faz 3: Core API Endpoints (7-11)
7. ⏳ API Routes: Dealers endpoints
8. ⏳ API Routes: Territories endpoint
9. ⏳ API Routes: POSM endpoints
10. ⏳ API Routes: Requests endpoints
11. ⏳ API Routes: Photos endpoints

### Faz 4: Docker & Deployment (12)
12. ⏳ Backend Dockerfile ve docker-compose.yml yapılandırması

### Faz 5: Frontend İskeleti (13)
13. ⏳ Frontend iskeleti: React + Vite projesi, routing, API client

### Faz 6: Frontend Sayfaları (14-21)
14. ⏳ Frontend: Login sayfası
15. ⏳ Frontend: Dashboard layout
16. ⏳ Frontend: Dashboard summary sayfası
17. ⏳ Frontend: New Request form
18. ⏳ Frontend: My Requests sayfası
19. ⏳ Frontend: All Requests sayfası
20. ⏳ Frontend: POSM Management sayfası
21. ⏳ Frontend: Request detail modal/popup

### Faz 7: Finalizasyon (22-25)
22. ⏳ Frontend Dockerfile ve docker-compose entegrasyonu
23. ⏳ Stil dosyalarını port et
24. ⏳ Error handling ve validation
25. ⏳ Test: Tüm endpointleri test et, frontend-backend entegrasyonu kontrol et

## 🔐 Güvenlik Özellikleri

- JWT tabanlı authentication (access + refresh token)
- Password hashing (bcrypt)
- Role-based authorization (user, admin, tech)
- Input validation (Pydantic schemas)
- SQL injection koruması (SQLAlchemy ORM)
- CORS yapılandırması
- Environment variables (.env) ile secrets yönetimi

## 📦 Docker Yapılandırması

### Services
- **db**: PostgreSQL 16
- **api**: FastAPI (port 8000)
- **frontend**: React build (Nginx, port 5173)

### Volumes
- `db_data`: PostgreSQL verileri
- `uploads`: Fotoğraf dosyaları

## 🚀 Çalıştırma

```bash
# Tüm servisleri başlat
docker-compose up -d

# Backend migration'ları çalıştır
docker-compose exec api alembic upgrade head

# Logları izle
docker-compose logs -f
```

## 📊 İlerleme Takibi

Her todo item tamamlandığında işaretlenecek ve bu dokümantasyon güncellenecek.
