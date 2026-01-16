#!/bin/bash
# 🚀 Sunucu PostgreSQL Kurulum ve Restore Script
# Kullanım: bash server_setup_script.sh

set -e  # Hata durumunda dur

echo "🚀 PostgreSQL Kurulum ve Restore Başlatılıyor..."

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. PostgreSQL Kurulumu
echo -e "${YELLOW}📦 PostgreSQL kurulumu kontrol ediliyor...${NC}"
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL bulunamadı, kuruluyor..."
    
    # OS tespiti
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        echo -e "${RED}❌ OS tespit edilemedi${NC}"
        exit 1
    fi
    
    if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
        sudo apt update
        sudo apt install -y postgresql-16 postgresql-contrib-16
    elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
        sudo dnf install -y postgresql16-server postgresql16
        sudo postgresql-16-setup initdb
    else
        echo -e "${RED}❌ Desteklenmeyen OS: $OS${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ PostgreSQL zaten kurulu${NC}"
fi

# PostgreSQL servisini başlat
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 2. Kullanıcı ve Veritabanı Oluşturma
echo -e "${YELLOW}👤 Kullanıcı ve veritabanı oluşturuluyor...${NC}"

sudo -u postgres psql << EOF
-- Kullanıcı oluştur (eğer yoksa)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'app') THEN
        CREATE USER app WITH PASSWORD 'app_password';
    ELSE
        ALTER USER app WITH PASSWORD 'app_password';
    END IF;
END
\$\$;

-- Veritabanı oluştur (eğer yoksa)
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

echo -e "${GREEN}✅ Kullanıcı ve veritabanı oluşturuldu${NC}"

# 3. Backup Dosyası Kontrolü
echo -e "${YELLOW}📁 Backup dosyası kontrol ediliyor...${NC}"

if [ ! -f "teknik_servis_backup.sql" ]; then
    echo -e "${RED}❌ teknik_servis_backup.sql dosyası bulunamadı!${NC}"
    echo "Lütfen backup dosyasını bu klasöre kopyalayın."
    exit 1
fi

echo -e "${GREEN}✅ Backup dosyası bulundu${NC}"

# 4. Restore
echo -e "${YELLOW}📥 Veritabanı restore ediliyor...${NC}"

sudo -u postgres psql -d teknik_servis < teknik_servis_backup.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Restore başarılı!${NC}"
else
    echo -e "${RED}❌ Restore hatası!${NC}"
    exit 1
fi

# 5. Bağlantı Testi
echo -e "${YELLOW}🔍 Bağlantı test ediliyor...${NC}"

sudo -u postgres psql -d teknik_servis -c "SELECT COUNT(*) as user_count FROM users;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bağlantı başarılı!${NC}"
    
    # Tablo sayısını göster
    TABLE_COUNT=$(sudo -u postgres psql -d teknik_servis -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo -e "${GREEN}📊 Toplam tablo sayısı: $TABLE_COUNT${NC}"
else
    echo -e "${RED}❌ Bağlantı hatası!${NC}"
    exit 1
fi

# 6. Remote Erişim Yapılandırması (Opsiyonel)
read -p "Remote erişim yapılandırması yapılsın mı? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🔧 Remote erişim yapılandırılıyor...${NC}"
    
    # postgresql.conf
    if [ -f /etc/postgresql/16/main/postgresql.conf ]; then
        sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf
        echo -e "${GREEN}✅ postgresql.conf güncellendi${NC}"
    fi
    
    # pg_hba.conf
    if [ -f /etc/postgresql/16/main/pg_hba.conf ]; then
        if ! grep -q "host.*teknik_servis.*app" /etc/postgresql/16/main/pg_hba.conf; then
            echo "host    teknik_servis    app    0.0.0.0/0    md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
            echo -e "${GREEN}✅ pg_hba.conf güncellendi${NC}"
        fi
    fi
    
    # PostgreSQL'i yeniden başlat
    sudo systemctl restart postgresql
    echo -e "${GREEN}✅ PostgreSQL yeniden başlatıldı${NC}"
    
    # Firewall (UFW)
    if command -v ufw &> /dev/null; then
        read -p "Firewall'da 5432 portunu açmak ister misiniz? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo ufw allow 5432/tcp
            echo -e "${GREEN}✅ Firewall kuralı eklendi${NC}"
        fi
    fi
fi

echo -e "${GREEN}🎉 Kurulum tamamlandı!${NC}"
echo ""
echo "📝 Bağlantı Bilgileri:"
echo "   Host: localhost (veya sunucu IP)"
echo "   Port: 5432"
echo "   Database: teknik_servis"
echo "   User: app"
echo "   Password: app_password"
echo ""
echo "🔗 Connection String:"
echo "   postgresql://app:app_password@localhost:5432/teknik_servis"
