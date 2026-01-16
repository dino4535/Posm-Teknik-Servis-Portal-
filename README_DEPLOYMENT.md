# 🚀 Ubuntu Sunucu Deployment Rehberi

## 📋 Hızlı Başlangıç

### 1. Sunucuya Bağlanın

```bash
ssh user@your-server-ip
```

### 2. Script'i İndirin ve Çalıştırın

```bash
# Script'i indirin (GitHub'dan clone edecekseniz zaten var)
# VEYA manuel olarak oluşturun

# Çalıştırılabilir yapın
chmod +x deploy_ubuntu_server.sh

# Çalıştırın
bash deploy_ubuntu_server.sh
```

Script otomatik olarak:
- ✅ Sistem güncellemesi yapar
- ✅ Docker ve Docker Compose kurar
- ✅ PostgreSQL kurar ve yapılandırır
- ✅ Projeyi GitHub'dan clone eder
- ✅ .env dosyası oluşturur (otomatik şifreler)
- ✅ Veritabanını restore eder (backup varsa)
- ✅ Docker servislerini başlatır
- ✅ Migration'ları çalıştırır
- ✅ Admin kullanıcı oluşturur

---

## 📥 Docker DB'den Veri Taşıma

### Yöntem 1: Otomatik Restore (Backup Dosyası Varsa)

Eğer `teknik_servis_backup.sql` dosyası proje klasöründeyse:

```bash
cd /opt/teknik-servis
chmod +x restore_docker_db.sh
bash restore_docker_db.sh
```

### Yöntem 2: Manuel Restore

#### Adım 1: Development Makineden Backup Alın

```bash
# Development makinede
cd c:\Users\Oguz\.cursor\Proje1
docker-compose exec db pg_dump -U app -d teknik_servis > teknik_servis_backup.sql
```

#### Adım 2: Backup'ı Sunucuya Kopyalayın

```bash
# Windows PowerShell'den
scp teknik_servis_backup.sql user@your-server-ip:/opt/teknik-servis/
```

#### Adım 3: Sunucuda Restore Edin

```bash
# Sunucuda
cd /opt/teknik-servis
sudo -u postgres psql -d teknik_servis < teknik_servis_backup.sql
```

---

## ⚙️ Manuel Kurulum (Script Kullanmak İstemiyorsanız)

### 1. Sistem Güncellemesi

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Docker Kurulumu

```bash
# Docker repository ekle
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker kur
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker'ı başlat
sudo systemctl start docker
sudo systemctl enable docker

# Kullanıcıyı docker grubuna ekle
sudo usermod -aG docker $USER
# Yeni oturum açmanız gerekebilir: newgrp docker
```

### 3. PostgreSQL Kurulumu

```bash
sudo apt install -y postgresql-16 postgresql-contrib-16
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 4. Projeyi Clone Edin

```bash
sudo mkdir -p /opt/teknik-servis
sudo chown $USER:$USER /opt/teknik-servis
cd /opt/teknik-servis
git clone https://github.com/dino4535/Posm-Teknik-Servis-Portal-.git .
```

### 5. .env Dosyası Oluşturun

```bash
nano .env
```

İçeriği (şifreleri değiştirin):

```env
# Database
DATABASE_URL=postgresql://app:your_password@localhost:5432/teknik_servis
DB_USER=app
DB_PASSWORD=your_secure_password_here
DB_NAME=teknik_servis
DB_PORT=5432

# Security
SECRET_KEY=your_very_secure_secret_key_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS_STR=https://yourdomain.com,https://www.yourdomain.com

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# File Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760

# Backup
BACKUP_DIR=backups

# API
API_V1_PREFIX=/api/v1

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Ports
API_PORT=8000
FRONTEND_PORT=80
```

### 6. PostgreSQL Kullanıcı ve Veritabanı Oluşturun

```bash
sudo -u postgres psql << EOF
CREATE USER app WITH PASSWORD 'your_password';
CREATE DATABASE teknik_servis OWNER app;
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO app;
EOF
```

### 7. Backup Restore (Varsa)

```bash
sudo -u postgres psql -d teknik_servis < teknik_servis_backup.sql
```

### 8. Docker Compose ile Başlatın

```bash
# docker-compose.yml'de DB servisini kaldırın veya comment out yapın
# Sonra:
docker compose up -d --build
```

### 9. Migration'ları Çalıştırın

```bash
docker compose exec api alembic upgrade head
```

### 10. Admin Kullanıcı Oluşturun

```bash
docker compose exec api python scripts/create_admin.py
```

---

## 🔧 Yapılandırma

### Docker Compose'da DB Servisini Kaldırma

`docker-compose.yml` dosyasında DB servisini comment out yapın veya silin:

```yaml
# db:
#   image: postgres:16-alpine
#   ...
```

API servisinin `depends_on` kısmını da kaldırın:

```yaml
api:
  # depends_on:
  #   db:
  #     condition: service_healthy
```

### DATABASE_URL Güncelleme

`docker-compose.yml` içinde:

```yaml
api:
  environment:
    - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
```

---

## 🔒 Güvenlik

### Firewall Yapılandırması

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### SSL Sertifikası (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Nginx Reverse Proxy (Önerilir)

```bash
sudo apt install nginx

# /etc/nginx/sites-available/teknik-servis
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Servis Yönetimi

### Servisleri Başlatma/Durdurma

```bash
# Tüm servisler
docker compose up -d
docker compose down

# Sadece API
docker compose up -d api
docker compose stop api

# PostgreSQL
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
```

### Logları İzleme

```bash
# Docker logları
docker compose logs -f api
docker compose logs -f frontend

# PostgreSQL logları
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Veritabanı Yedekleme

```bash
# Manuel backup
sudo -u postgres pg_dump -d teknik_servis > backup_$(date +%Y%m%d).sql

# Otomatik backup (cron)
0 2 * * * sudo -u postgres pg_dump -d teknik_servis | gzip > /opt/teknik-servis/backups/backup_$(date +\%Y\%m\%d).sql.gz
```

---

## 🐛 Troubleshooting

### PostgreSQL Bağlantı Hatası

```bash
# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql

# Port dinleniyor mu?
sudo netstat -tlnp | grep 5432

# Kullanıcı yetkileri
sudo -u postgres psql -d teknik_servis -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;"
```

### Docker Servisleri Çalışmıyor

```bash
# Docker durumu
docker compose ps
docker compose logs api

# Yeniden başlat
docker compose restart api
```

### Migration Hataları

```bash
# Migration durumu
docker compose exec api alembic current

# Migration'ı geri al
docker compose exec api alembic downgrade -1

# Tüm migration'ları çalıştır
docker compose exec api alembic upgrade head
```

---

## 📝 Önemli Notlar

1. **.env Dosyası**: Asla commit etmeyin, güvenli tutun
2. **Backup**: Düzenli backup alın
3. **Güncellemeler**: Sistem ve paket güncellemelerini düzenli yapın
4. **Monitoring**: Logları düzenli kontrol edin
5. **Security**: Firewall ve SSL kullanın

---

## 🎯 Sonraki Adımlar

1. ✅ Domain name yapılandırması
2. ✅ Nginx reverse proxy kurulumu
3. ✅ SSL sertifikası (Let's Encrypt)
4. ✅ Monitoring kurulumu
5. ✅ Otomatik backup yapılandırması
