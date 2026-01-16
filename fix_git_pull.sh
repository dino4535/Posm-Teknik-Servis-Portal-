#!/bin/bash
# 🔧 Git Pull Sorununu Çözme Scripti
# Kullanım: bash fix_git_pull.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Git pull sorunu çözülüyor...${NC}"

cd /opt/teknik-servis

# Seçenek 1: Local değişiklikleri stash yap
echo -e "${YELLOW}📦 Local değişiklikler stash'leniyor...${NC}"
git stash

# Pull yap
echo -e "${YELLOW}📥 Güncellemeler çekiliyor...${NC}"
git pull

# Stash'lenen değişiklikleri geri yükle (opsiyonel)
read -p "Stash'lenen değişiklikleri geri yüklemek ister misiniz? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git stash pop
    echo -e "${GREEN}✅ Değişiklikler geri yüklendi${NC}"
else
    echo -e "${YELLOW}⚠️  Değişiklikler stash'te saklanıyor (git stash list ile görebilirsiniz)${NC}"
fi

echo -e "${GREEN}✅ Git pull tamamlandı!${NC}"
