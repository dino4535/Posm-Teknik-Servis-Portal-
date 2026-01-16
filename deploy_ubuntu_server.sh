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
# Database - Sunucu PostgreSQL
DATABASE_URL=postgresql://app:${DB_PASSWORD}@localhost:5432/teknik_servis
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
API_PORT=8000
FRONTEND_PORT=80
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

# 10. Backup Dosyası Kontrolü ve Restore
echo -e "${YELLOW}📥 Veritabanı backup'ı kontrol ediliyor...${NC}"

if [ -f "teknik_servis_backup.sql" ]; then
    echo "Backup dosyası bulundu, restore ediliyor..."
    sudo -u postgres psql -d teknik_servis < teknik_servis_backup.sql
    echo -e "${GREEN}✅ Veritabanı restore edildi${NC}"
else
    echo -e "${YELLOW}⚠️  Backup dosyası bulunamadı, boş veritabanı ile devam ediliyor${NC}"
    echo "Migration'lar çalıştırılacak..."
fi

# 11. Docker Compose ile Servisleri Başlatma
echo -e "${YELLOW}🐳 Docker servisleri başlatılıyor...${NC}"

# docker-compose.yml'de DB servisini kaldır (sunucu PostgreSQL kullanıyoruz)
# Geçici olarak DB servisini comment out edelim
sed -i 's/^  db:/  # db:/' docker-compose.yml
sed -i 's/^    image: postgres:16-alpine/#    image: postgres:16-alpine/' docker-compose.yml
sed -i 's/^    container_name: teknik_servis_db/#    container_name: teknik_servis_db/' docker-compose.yml
sed -i 's/^    environment:/#    environment:/' docker-compose.yml
sed -i 's/^      POSTGRES_USER:/#      POSTGRES_USER:/' docker-compose.yml
sed -i 's/^      POSTGRES_PASSWORD:/#      POSTGRES_PASSWORD:/' docker-compose.yml
sed -i 's/^      POSTGRES_DB:/#      POSTGRES_DB:/' docker-compose.yml
sed -i 's/^    volumes:/#    volumes:/' docker-compose.yml
sed -i 's/^      - db_data:/#      - db_data:/' docker-compose.yml
sed -i 's/^    ports:/#    ports:/' docker-compose.yml
sed -i 's/^      - "${DB_PORT:-5432}:5432"/#      - "${DB_PORT:-5432}:5432"/' docker-compose.yml
sed -i 's/^    healthcheck:/#    healthcheck:/' docker-compose.yml
sed -i 's/^      test:/#      test:/' docker-compose.yml
sed -i 's/^      interval:/#      interval:/' docker-compose.yml
sed -i 's/^      timeout:/#      timeout:/' docker-compose.yml
sed -i 's/^      retries:/#      retries:/' docker-compose.yml
sed -i 's/^    networks:/#    networks:/' docker-compose.yml
sed -i 's/^      - app_network/#      - app_network/' docker-compose.yml

# API servisinin depends_on kısmını kaldır
sed -i 's/^    depends_on:/#    depends_on:/' docker-compose.yml
sed -i 's/^      db:/#      db:/' docker-compose.yml
sed -i 's/^        condition: service_healthy/#        condition: service_healthy/' docker-compose.yml

# DATABASE_URL'i güncelle (sunucu PostgreSQL için)
sed -i "s|DATABASE_URL=postgresql://\${DB_USER:-app}:\${DB_PASSWORD:-app_password}@db:5432/\${DB_NAME:-teknik_servis}|DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@localhost:5432/\${DB_NAME}|" docker-compose.yml

# API servisinin environment kısmını güncelle
sed -i 's/- DATABASE_URL=/# - DATABASE_URL=/' docker-compose.yml

# Volumes kısmından db_data'yı kaldır
sed -i 's/^  db_data:/#  db_data:/' docker-compose.yml
sed -i 's/^    driver: local/#    driver: local/' docker-compose.yml

# Docker Compose ile servisleri başlat
docker compose up -d --build

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
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS
    sudo ufw allow 8000/tcp # API (opsiyonel, reverse proxy kullanıyorsanız kapatın)
    
    read -p "Firewall'u aktif etmek ister misiniz? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw --force enable
        echo -e "${GREEN}✅ Firewall aktif edildi${NC}"
    fi
fi

# 16. Servis Durumu Kontrolü
echo -e "${YELLOW}🔍 Servis durumu kontrol ediliyor...${NC}"

sleep 3

# PostgreSQL kontrolü
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL çalışıyor${NC}"
else
    echo -e "${RED}❌ PostgreSQL çalışmıyor!${NC}"
fi

# Docker servisleri kontrolü
echo -e "${YELLOW}🐳 Docker servisleri:${NC}"
docker compose -f docker-compose.prod.yml ps

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
echo -e "   Frontend: http://${SERVER_IP}"
echo -e "   API: http://${SERVER_IP}:8000 (sadece localhost'tan erişilebilir)"
echo -e "   API Docs: http://localhost:8000/docs (sunucu üzerinden)"
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
