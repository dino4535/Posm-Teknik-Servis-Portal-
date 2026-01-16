#!/bin/bash
# 🚀 Ubuntu Sunucu Otomatik Kurulum Scripti
# Kullanım: bash deploy_ubuntu_server.sh

set -e  # Hata durumunda dur

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Teknik Servis Portalı - Ubuntu Sunucu Kurulumu${NC}"
echo "=================================================="
echo ""

# 1. Sistem Güncellemesi
echo -e "${YELLOW}📦 Sistem güncelleniyor...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. Gerekli Paketlerin Kurulumu
echo -e "${YELLOW}📦 Gerekli paketler kuruluyor...${NC}"
sudo apt install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 3. PostgreSQL Repository Ekleme
echo -e "${YELLOW}📦 PostgreSQL repository ekleniyor...${NC}"
if ! grep -q "apt.postgresql.org" /etc/apt/sources.list.d/pgdg.list 2>/dev/null; then
    # PostgreSQL official repository ekle
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    
    # GPG key ekle
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    
    # Repository'yi güncelle
    sudo apt update
    echo -e "${GREEN}✅ PostgreSQL repository eklendi${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL repository zaten mevcut${NC}"
fi

# PostgreSQL 16 kurulumu
echo -e "${YELLOW}📦 PostgreSQL 16 kuruluyor...${NC}"
sudo apt install -y postgresql-16 postgresql-contrib-16

# 4. Docker Kurulumu
echo -e "${YELLOW}🐳 Docker kurulumu kontrol ediliyor...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker kuruluyor..."
    # Docker repository ekle
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Docker'ı başlat
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Kullanıcıyı docker grubuna ekle (sudo olmadan çalışması için)
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker kuruldu${NC}"
else
    echo -e "${GREEN}✅ Docker zaten kurulu${NC}"
fi

# 5. Docker Compose Kurulumu
echo -e "${YELLOW}🐳 Docker Compose kurulumu kontrol ediliyor...${NC}"
if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose kuruluyor..."
    # Docker Compose plugin zaten docker-ce ile geldi
    echo -e "${GREEN}✅ Docker Compose kuruldu${NC}"
else
    echo -e "${GREEN}✅ Docker Compose zaten kurulu${NC}"
fi

# 6. Proje Klasörü Oluşturma
echo -e "${YELLOW}📁 Proje klasörü oluşturuluyor...${NC}"
PROJECT_DIR="/opt/teknik-servis"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 7. GitHub'dan Projeyi Clone Etme
echo -e "${YELLOW}📥 GitHub'dan proje indiriliyor...${NC}"
cd $PROJECT_DIR

if [ -d ".git" ]; then
    echo "Proje zaten clone edilmiş, güncelleniyor..."
    git pull
else
    echo "Proje clone ediliyor..."
    read -p "GitHub repository URL'i (Enter = otomatik): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        REPO_URL="https://github.com/dino4535/Posm-Teknik-Servis-Portal-.git"
    fi
    git clone $REPO_URL .
fi

echo -e "${GREEN}✅ Proje indirildi${NC}"

# 8. .env Dosyası Oluşturma
echo -e "${YELLOW}⚙️  .env dosyası oluşturuluyor...${NC}"

# Sunucu IP'sini otomatik al
SERVER_IP=$(hostname -I | awk '{print $1}')

# Güçlü şifre oluştur
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -hex 32)

# .env dosyası oluştur
cat > .env << EOF
# Database - Docker PostgreSQL container
DATABASE_URL=postgresql://app:${DB_PASSWORD}@db:5432/teknik_servis
DB_USER=app
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=teknik_servis
DB_PORT=5432

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Production domain'lerinizi ekleyin
CORS_ORIGINS_STR=https://yourdomain.com,https://www.yourdomain.com

# File Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760

# Backup
BACKUP_DIR=backups

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=false

# API
API_V1_PREFIX=/api/v1

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Ports
API_PORT=8001
FRONTEND_PORT=5173

# API URL for frontend (use server IP)
SERVER_IP=\$(curl -s ifconfig.me || hostname -I | awk '{print \$1}')
API_URL=http://\${SERVER_IP}:8001
EOF

echo -e "${GREEN}✅ .env dosyası oluşturuldu${NC}"
echo -e "${YELLOW}⚠️  ÖNEMLİ: .env dosyasındaki şifreleri not edin!${NC}"
echo -e "${BLUE}   DB_PASSWORD: ${DB_PASSWORD}${NC}"
echo -e "${BLUE}   SECRET_KEY: ${SECRET_KEY}${NC}"

# 9. PostgreSQL Yapılandırması
echo -e "${YELLOW}🗄️  PostgreSQL yapılandırılıyor...${NC}"

# PostgreSQL servisini başlat
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Kullanıcı ve veritabanı oluştur
sudo -u postgres psql << EOF
-- Kullanıcı oluştur
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'app') THEN
        CREATE USER app WITH PASSWORD '${DB_PASSWORD}';
    ELSE
        ALTER USER app WITH PASSWORD '${DB_PASSWORD}';
    END IF;
END
\$\$;

-- Veritabanı oluştur
SELECT 'CREATE DATABASE teknik_servis OWNER app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'teknik_servis')\gexec

-- Yetkileri ver
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO app;
\c teknik_servis
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app;
EOF

echo -e "${GREEN}✅ PostgreSQL yapılandırıldı${NC}"

# 10. Backup Dosyası Kontrolü (Docker container başladıktan sonra restore edilecek)
echo -e "${YELLOW}📥 Veritabanı backup'ı kontrol ediliyor...${NC}"

if [ -f "teknik_servis_backup.sql" ]; then
    echo -e "${GREEN}✅ Backup dosyası bulundu (Docker container başladıktan sonra restore edilecek)${NC}"
    BACKUP_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Backup dosyası bulunamadı, boş veritabanı ile devam ediliyor${NC}"
    echo "Migration'lar çalıştırılacak..."
    BACKUP_EXISTS=false
fi

# 11. Docker Compose Production Dosyası Oluşturma
echo -e "${YELLOW}🐳 Docker Compose production dosyası oluşturuluyor...${NC}"

# .env dosyasındaki DATABASE_URL'i Docker container için güncelle (db servisi kullanılacak)
sed -i "s|@host.docker.internal:5432|@db:5432|" .env

# Production docker-compose dosyası oluştur (PostgreSQL, API ve Frontend - hepsi Docker'da)
cat > docker-compose.prod.yml << 'DOCKEREOF'
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    container_name: teknik_servis_db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=tr_TR.UTF-8"
      LC_ALL: tr_TR.UTF-8
      LANG: tr_TR.UTF-8
    volumes:
      - db_data_prod:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_network
    restart: unless-stopped

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: teknik_servis_api
    env_file:
      - .env
    ports:
      - "0.0.0.0:8001:8000"
    volumes:
      - ./backend:/app
      - uploads_prod:/app/uploads
      - backups_prod:/app/backups
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: \${API_URL}
    container_name: teknik_servis_frontend
    ports:
      - "0.0.0.0:5173:80"
    depends_on:
      - api
    networks:
      - app_network
    restart: unless-stopped

volumes:
  db_data_prod:
    driver: local
  uploads_prod:
    driver: local
  backups_prod:
    driver: local

networks:
  app_network:
    driver: bridge
DOCKEREOF

echo -e "${GREEN}✅ Docker Compose production dosyası oluşturuldu${NC}"

# 12. Docker Compose ile Servisleri Başlatma
echo -e "${YELLOW}🐳 Docker servisleri başlatılıyor (PostgreSQL, API ve Frontend)...${NC}"

# Sunucudaki PostgreSQL servisini durdur (Docker container kullanacağız)
echo -e "${YELLOW}🛑 Sunucu PostgreSQL servisi durduruluyor...${NC}"
if sudo systemctl is-active --quiet postgresql 2>/dev/null; then
    sudo systemctl stop postgresql
    sudo systemctl disable postgresql
    echo -e "${GREEN}✅ Sunucu PostgreSQL servisi durduruldu${NC}"
else
    echo -e "${GREEN}✅ Sunucu PostgreSQL servisi zaten durdurulmuş${NC}"
fi

# Port 5432'i kullanan process'i kontrol et ve durdur
PORT_5432_PID=$(sudo lsof -ti:5432 2>/dev/null || echo "")
if [ ! -z "$PORT_5432_PID" ]; then
    echo -e "${YELLOW}⚠️  Port 5432 kullanılıyor (PID: $PORT_5432_PID), durduruluyor...${NC}"
    sudo kill -9 $PORT_5432_PID 2>/dev/null || true
    sleep 2
fi

# Önce DB container'ını başlat
echo -e "${YELLOW}🗄️  PostgreSQL container başlatılıyor...${NC}"
docker compose -f docker-compose.prod.yml up -d db

# PostgreSQL'in hazır olmasını bekle
echo -e "${YELLOW}⏳ PostgreSQL'in hazır olması bekleniyor...${NC}"
sleep 10

# PostgreSQL container'ında kullanıcı ve veritabanı oluştur
# Not: POSTGRES_USER environment variable ile belirlenen kullanıcı superuser olur
echo -e "${YELLOW}👤 PostgreSQL kullanıcı ve veritabanı kontrol ediliyor...${NC}"

# .env dosyasından DB_USER'ı oku
DB_USER_FROM_ENV=$(grep "^DB_USER=" .env | cut -d '=' -f2)

# PostgreSQL container'ında kullanıcı zaten POSTGRES_USER ile oluşturulmuş olmalı
# Sadece veritabanı ve yetkileri kontrol edelim
docker compose -f docker-compose.prod.yml exec -T db psql -U ${DB_USER_FROM_ENV} -d postgres << EOF
-- Veritabanı oluştur (eğer yoksa) - UTF-8 encoding ile
SELECT 'CREATE DATABASE teknik_servis OWNER ${DB_USER_FROM_ENV} ENCODING ''UTF8'' LC_COLLATE=''tr_TR.UTF-8'' LC_CTYPE=''tr_TR.UTF-8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'teknik_servis')\gexec

-- Yetkileri ver
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO ${DB_USER_FROM_ENV};
\c teknik_servis
-- Client encoding'i UTF-8 yap
SET client_encoding = 'UTF8';
-- Mevcut tablolar için encoding kontrolü
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER_FROM_ENV};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER_FROM_ENV};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER_FROM_ENV};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER_FROM_ENV};
EOF

# Backup restore (varsa)
if [ "$BACKUP_EXISTS" = true ]; then
    echo -e "${YELLOW}📥 Backup restore ediliyor...${NC}"
    docker compose -f docker-compose.prod.yml exec -T db psql -U app -d teknik_servis < teknik_servis_backup.sql
    echo -e "${GREEN}✅ Backup restore edildi${NC}"
fi

# Tüm servisleri başlat
echo -e "${YELLOW}🚀 Tüm servisler başlatılıyor...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

echo -e "${GREEN}✅ Docker servisleri başlatıldı${NC}"

# 13. Migration'ları Çalıştırma
echo -e "${YELLOW}🔄 Database migration'ları çalıştırılıyor...${NC}"

sleep 10  # API'nin başlaması için bekle

docker compose -f docker-compose.prod.yml exec api alembic upgrade head

echo -e "${GREEN}✅ Migration'lar tamamlandı${NC}"

# 14. Admin Kullanıcı Oluşturma
echo -e "${YELLOW}👤 Admin kullanıcı oluşturuluyor...${NC}"

docker compose -f docker-compose.prod.yml exec api python scripts/create_admin.py

echo -e "${GREEN}✅ Admin kullanıcı oluşturuldu${NC}"

# 15. Firewall Yapılandırması
echo -e "${YELLOW}🔥 Firewall yapılandırılıyor...${NC}"

if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 5173/tcp # Frontend
    sudo ufw allow 443/tcp  # HTTPS
    sudo ufw allow 8001/tcp # API (opsiyonel, reverse proxy kullanıyorsanız kapatın)
    
    read -p "Firewall'u aktif etmek ister misiniz? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw --force enable
        echo -e "${GREEN}✅ Firewall aktif edildi${NC}"
    fi
fi

# 16. Servis Durumu Kontrolü
echo -e "${YELLOW}🔍 Servis durumu kontrol ediliyor...${NC}"

sleep 5

# Docker servisleri kontrolü
echo -e "${YELLOW}🐳 Docker servisleri:${NC}"
docker compose -f docker-compose.prod.yml ps

# PostgreSQL container kontrolü
if docker compose -f docker-compose.prod.yml ps | grep -q "teknik_servis_db.*Up"; then
    echo -e "${GREEN}✅ PostgreSQL container çalışıyor${NC}"
else
    echo -e "${RED}❌ PostgreSQL container çalışmıyor!${NC}"
fi

# 17. Özet Bilgiler
echo ""
echo -e "${BLUE}=================================================="
echo -e "🎉 Kurulum Tamamlandı!${NC}"
echo -e "${BLUE}=================================================="
echo ""
echo -e "${GREEN}📋 Önemli Bilgiler:${NC}"
echo ""
echo -e "📁 Proje Klasörü: ${PROJECT_DIR}"
echo -e "🗄️  Database: teknik_servis"
echo -e "👤 DB User: app"
echo -e "🔑 DB Password: ${DB_PASSWORD}"
echo -e "🔐 Secret Key: ${SECRET_KEY}"
echo ""
echo -e "${YELLOW}⚠️  Bu bilgileri güvenli bir yerde saklayın!${NC}"
echo ""
echo -e "${GREEN}🌐 Erişim Bilgileri:${NC}"
echo -e "   Frontend: http://${SERVER_IP}:5173"
echo -e "   API: http://localhost:8001 (sadece sunucu üzerinden)"
echo -e "   API Docs: http://localhost:8001/docs (sunucu üzerinden)"
echo ""
echo -e "${YELLOW}⚠️  Not: API sadece localhost'tan erişilebilir (güvenlik için)${NC}"
echo -e "   Nginx reverse proxy kullanarak dışarıdan erişim sağlayabilirsiniz"
echo ""
echo -e "${GREEN}📝 Sonraki Adımlar:${NC}"
echo "   1. Domain name'inizi DNS'te bu sunucuya yönlendirin"
echo "   2. Nginx reverse proxy kurun (opsiyonel ama önerilir)"
echo "   3. SSL sertifikası kurun (Let's Encrypt)"
echo "   4. .env dosyasındaki CORS_ORIGINS_STR'i güncelleyin"
echo ""
echo -e "${BLUE}=================================================="
