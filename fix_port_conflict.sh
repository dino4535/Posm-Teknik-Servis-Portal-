#!/bin/bash
# 🔧 Port Çakışması Çözme Scripti
# Kullanım: bash fix_port_conflict.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Port çakışması çözülüyor...${NC}"

cd /opt/teknik-servis

# 1. Eski Docker container'larını durdur
echo -e "${YELLOW}🛑 Eski Docker container'ları durduruluyor...${NC}"

# Tüm teknik-servis container'larını durdur
docker ps -a --filter "name=teknik_servis" --format "{{.Names}}" | xargs -r docker stop
docker ps -a --filter "name=teknik_servis" --format "{{.Names}}" | xargs -r docker rm

# docker-compose ile de durdur
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true

echo -e "${GREEN}✅ Eski container'lar durduruldu${NC}"

# 2. Port 8000'i kullanan process'i bul ve durdur
echo -e "${YELLOW}🔍 Port 8000'i kullanan process kontrol ediliyor...${NC}"

PORT_8000_PID=$(sudo lsof -ti:8000 2>/dev/null || echo "")

if [ ! -z "$PORT_8000_PID" ]; then
    echo -e "${YELLOW}⚠️  Port 8000 kullanılıyor (PID: $PORT_8000_PID)${NC}"
    read -p "Bu process'i durdurmak ister misiniz? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo kill -9 $PORT_8000_PID
        echo -e "${GREEN}✅ Process durduruldu${NC}"
    else
        echo -e "${YELLOW}⚠️  Process durdurulmadı, manuel olarak durdurun${NC}"
    fi
else
    echo -e "${GREEN}✅ Port 8000 boş${NC}"
fi

# 3. Port 80'i kullanan process'i kontrol et
echo -e "${YELLOW}🔍 Port 80'i kullanan process kontrol ediliyor...${NC}"

PORT_80_PID=$(sudo lsof -ti:80 2>/dev/null || echo "")

if [ ! -z "$PORT_80_PID" ]; then
    echo -e "${YELLOW}⚠️  Port 80 kullanılıyor (PID: $PORT_80_PID)${NC}"
    echo "Process bilgisi:"
    sudo ps -p $PORT_80_PID -o pid,cmd
    read -p "Bu process'i durdurmak ister misiniz? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo kill -9 $PORT_80_PID
        echo -e "${GREEN}✅ Process durduruldu${NC}"
    else
        echo -e "${YELLOW}⚠️  Process durdurulmadı, manuel olarak durdurun${NC}"
    fi
else
    echo -e "${GREEN}✅ Port 80 boş${NC}"
fi

# 4. Docker network'leri temizle
echo -e "${YELLOW}🧹 Docker network'leri temizleniyor...${NC}"
docker network prune -f

echo -e "${GREEN}✅ Temizlik tamamlandı!${NC}"
echo ""
echo -e "${BLUE}📝 Şimdi deployment script'ini tekrar çalıştırabilirsiniz:${NC}"
echo "   bash deploy_ubuntu_server.sh"
