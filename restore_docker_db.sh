#!/bin/bash
# 📥 Docker DB'den Sunucu PostgreSQL'e Restore Scripti
# Kullanım: bash restore_docker_db.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📥 Docker DB'den Sunucu PostgreSQL'e Restore${NC}"
echo "=================================================="
echo ""

# 1. Backup dosyası kontrolü
echo -e "${YELLOW}📁 Backup dosyası kontrol ediliyor...${NC}"

if [ -f "teknik_servis_backup.sql" ]; then
    echo -e "${GREEN}✅ Backup dosyası bulundu: teknik_servis_backup.sql${NC}"
    BACKUP_FILE="teknik_servis_backup.sql"
elif [ -f "../teknik_servis_backup.sql" ]; then
    echo -e "${GREEN}✅ Backup dosyası bulundu: ../teknik_servis_backup.sql${NC}"
    BACKUP_FILE="../teknik_servis_backup.sql"
else
    echo -e "${RED}❌ Backup dosyası bulunamadı!${NC}"
    echo ""
    echo "Backup dosyasını şu şekilde alabilirsiniz:"
    echo "  1. Development makinede:"
    echo "     docker-compose exec db pg_dump -U app -d teknik_servis > teknik_servis_backup.sql"
    echo ""
    echo "  2. Sunucuya kopyalayın:"
    echo "     scp teknik_servis_backup.sql user@server:/opt/teknik-servis/"
    echo ""
    exit 1
fi

# 2. .env dosyasından DB bilgilerini oku
echo -e "${YELLOW}⚙️  .env dosyasından DB bilgileri okunuyor...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env dosyası bulunamadı!${NC}"
    echo "Önce deploy_ubuntu_server.sh scriptini çalıştırın."
    exit 1
fi

# DB bilgilerini .env'den oku
DB_USER=$(grep "^DB_USER=" .env | cut -d '=' -f2)
DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d '=' -f2)
DB_NAME=$(grep "^DB_NAME=" .env | cut -d '=' -f2)

if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo -e "${RED}❌ .env dosyasında DB bilgileri eksik!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ DB bilgileri okundu${NC}"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"

# 3. PostgreSQL bağlantı testi
echo -e "${YELLOW}🔍 PostgreSQL bağlantısı test ediliyor...${NC}"

if ! sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL çalışmıyor!${NC}"
    echo "PostgreSQL'i başlatın: sudo systemctl start postgresql"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL çalışıyor${NC}"

# 4. Veritabanı var mı kontrol et
echo -e "${YELLOW}🗄️  Veritabanı kontrol ediliyor...${NC}"

DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [ "$DB_EXISTS" != "1" ]; then
    echo "Veritabanı bulunamadı, oluşturuluyor..."
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    echo -e "${GREEN}✅ Veritabanı oluşturuldu${NC}"
else
    echo -e "${GREEN}✅ Veritabanı mevcut${NC}"
    
    # Mevcut verileri silmek ister misiniz?
    read -p "Mevcut veriler silinecek, devam edilsin mi? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Mevcut veritabanı temizleniyor..."
        sudo -u postgres psql -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
        sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
        echo -e "${GREEN}✅ Veritabanı temizlendi${NC}"
    fi
fi

# 5. Backup restore
echo -e "${YELLOW}📥 Backup restore ediliyor...${NC}"
echo "Bu işlem biraz zaman alabilir..."

sudo -u postgres psql -d $DB_NAME < $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Restore başarılı!${NC}"
else
    echo -e "${RED}❌ Restore hatası!${NC}"
    exit 1
fi

# 6. Yetkileri kontrol et ve düzelt
echo -e "${YELLOW}🔐 Veritabanı yetkileri kontrol ediliyor...${NC}"

sudo -u postgres psql -d $DB_NAME << EOF
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

echo -e "${GREEN}✅ Yetkiler güncellendi${NC}"

# 7. Veri kontrolü
echo -e "${YELLOW}🔍 Veri kontrol ediliyor...${NC}"

TABLE_COUNT=$(sudo -u postgres psql -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
USER_COUNT=$(sudo -u postgres psql -d $DB_NAME -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

echo -e "${GREEN}✅ Tablo sayısı: $TABLE_COUNT${NC}"
if [ "$USER_COUNT" != "0" ]; then
    echo -e "${GREEN}✅ Kullanıcı sayısı: $USER_COUNT${NC}"
fi

# 8. Migration kontrolü
echo -e "${YELLOW}🔄 Migration durumu kontrol ediliyor...${NC}"

echo "Migration'ları çalıştırmak için:"
echo "  docker compose exec api alembic upgrade head"

echo ""
echo -e "${BLUE}=================================================="
echo -e "${GREEN}🎉 Restore Tamamlandı!${NC}"
echo -e "${BLUE}=================================================="
echo ""
echo -e "${GREEN}📋 Sonraki Adımlar:${NC}"
echo "   1. Migration'ları çalıştırın: docker compose exec api alembic upgrade head"
echo "   2. Admin kullanıcıyı kontrol edin: docker compose exec api python scripts/create_admin.py"
echo "   3. API'yi test edin: curl http://localhost:8000/health"
echo ""
