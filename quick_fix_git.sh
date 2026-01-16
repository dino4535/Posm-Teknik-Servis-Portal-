#!/bin/bash
# 🔧 Hızlı Git Pull Düzeltme
# Kullanım: bash quick_fix_git.sh

cd /opt/teknik-servis

# Local değişiklikleri kaydetmeden sil (remote versiyonu kullan)
git reset --hard HEAD
git pull

echo "✅ Git güncellemesi tamamlandı!"
