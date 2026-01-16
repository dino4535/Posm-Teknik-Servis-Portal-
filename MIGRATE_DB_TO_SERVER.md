# 🚀 Docker DB'yi Sunucuya Taşıma Rehberi

## 📋 Adım Adım İşlem

### 1️⃣ Mevcut Docker DB'den Dump Alma

**Yerel makinede (development):**

```bash
# Proje klasörüne gidin
cd c:\Users\Oguz\.cursor\Proje1

# Tüm veritabanını dump alın (schema + data)
docker-compose exec db pg_dump -U app -d teknik_servis -F c -f /tmp/teknik_servis_backup.dump

# Dump'ı container'dan çıkarın
docker-compose cp db:/tmp/teknik_servis_backup.dump ./teknik_servis_backup.dump

# VEYA daha basit yöntem (SQL format):
docker-compose exec db pg_dump -U app -d teknik_servis > teknik_servis_backup.sql
```

**Alternatif: SQL format (daha kolay):**

```bash
docker-compose exec db pg_dump -U app -d teknik_servis --clean --if-exists > teknik_servis_backup.sql
```

---

### 2️⃣ Sunucuya PostgreSQL Kurulumu

**Ubuntu/Debian sunucuda:**

```bash
# SSH ile sunucuya bağlanın
ssh user@your-server-ip

# PostgreSQL 16 kurulumu
sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# PostgreSQL servisini başlatın
sudo systemctl start postgresql
sudo systemctl enable postgresql

# PostgreSQL durumunu kontrol edin
sudo systemctl status postgresql
```

**CentOS/RHEL sunucuda:**

```bash
# PostgreSQL repository ekleyin
sudo dnf install -y postgresql16-server postgresql16

# PostgreSQL'i başlatın
sudo postgresql-16-setup initdb
sudo systemctl start postgresql-16
sudo systemctl enable postgresql-16
```

---

### 3️⃣ Kullanıcı ve Veritabanı Oluşturma

**Sunucuda PostgreSQL'e bağlanın:**

```bash
# PostgreSQL superuser olarak bağlanın
sudo -u postgres psql
```

**PostgreSQL içinde komutlar:**

```sql
-- Mevcut kullanıcı adı ve şifre ile kullanıcı oluştur
-- (docker-compose.yml'den: app / app_password)
CREATE USER app WITH PASSWORD 'app_password';

-- Veritabanı oluştur
CREATE DATABASE teknik_servis OWNER app;

-- Tüm yetkileri ver
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO app;

-- PostgreSQL'den çık
\q
```

**Alternatif: Tek komutla (bash'den):**

```bash
sudo -u postgres psql << EOF
CREATE USER app WITH PASSWORD 'app_password';
CREATE DATABASE teknik_servis OWNER app;
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO app;
EOF
```

---

### 4️⃣ Remote Erişim İçin Yapılandırma (Opsiyonel)

**Eğer uygulama farklı bir sunucudaysa:**

```bash
# postgresql.conf dosyasını düzenleyin
sudo nano /etc/postgresql/16/main/postgresql.conf

# Şu satırı bulun ve değiştirin:
# listen_addresses = 'localhost'
listen_addresses = '*'  # VEYA sadece uygulama sunucusu IP'si

# Dosyayı kaydedin (Ctrl+O, Enter, Ctrl+X)
```

**pg_hba.conf dosyasını düzenleyin:**

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

**Dosyanın sonuna ekleyin:**

```
# Remote connections (sadece güvenilir IP'lerden)
host    teknik_servis    app    YOUR_APP_SERVER_IP/32    md5

# VEYA tüm IP'lerden (GÜVENLİK RİSKİ - sadece test için)
host    teknik_servis    app    0.0.0.0/0    md5
```

**PostgreSQL'i yeniden başlatın:**

```bash
sudo systemctl restart postgresql
```

**Firewall kuralları (UFW):**

```bash
# PostgreSQL port'unu açın (sadece uygulama sunucusundan)
sudo ufw allow from YOUR_APP_SERVER_IP to any port 5432

# VEYA tüm IP'lerden (GÜVENLİK RİSKİ)
sudo ufw allow 5432/tcp
```

---

### 5️⃣ Backup'ı Sunucuya Yükleme

**Yöntem 1: SCP ile (önerilen)**

```bash
# Yerel makineden (Windows PowerShell veya WSL)
scp teknik_servis_backup.sql user@your-server-ip:/tmp/

# Sunucuda restore edin
ssh user@your-server-ip
sudo -u postgres psql -d teknik_servis < /tmp/teknik_servis_backup.sql
```

**Yöntem 2: Doğrudan pipe ile**

```bash
# Yerel makineden
docker-compose exec db pg_dump -U app -d teknik_servis | ssh user@your-server-ip "sudo -u postgres psql -d teknik_servis"
```

**Yöntem 3: pg_restore (Custom format için)**

```bash
# Sunucuda
sudo -u postgres pg_restore -d teknik_servis -U postgres /tmp/teknik_servis_backup.dump
```

---

### 6️⃣ Migration'ları Çalıştırma

**Sunucuda Alembic migration'ları:**

```bash
# Uygulama sunucusuna bağlanın
ssh user@your-app-server-ip

# Proje klasörüne gidin
cd /path/to/your/project

# Migration'ları çalıştırın
docker-compose exec api alembic upgrade head

# VEYA lokal Python ile
cd backend
python -m alembic upgrade head
```

---

### 7️⃣ Environment Variables Güncelleme

**Sunucuda `.env.production` dosyasını oluşturun:**

```bash
nano .env.production
```

**İçeriği:**

```env
# Database - Sunucu IP'si ile
DATABASE_URL=postgresql://app:app_password@YOUR_DB_SERVER_IP:5432/teknik_servis
DB_USER=app
DB_PASSWORD=app_password
DB_NAME=teknik_servis
DB_PORT=5432

# Diğer production ayarları...
SECRET_KEY=your_production_secret_key_here
CORS_ORIGINS_STR=https://yourdomain.com
ENVIRONMENT=production
DEBUG=false
```

**VEYA aynı sunucudaysa:**

```env
DATABASE_URL=postgresql://app:app_password@localhost:5432/teknik_servis
```

---

### 8️⃣ Docker Compose Güncelleme

**`docker-compose.production.yml` dosyasını düzenleyin:**

```yaml
services:
  api:
    environment:
      # DB servisini kaldırın, direkt connection string kullanın
      - DATABASE_URL=postgresql://app:app_password@YOUR_DB_SERVER_IP:5432/teknik_servis
    # depends_on: db kısmını kaldırın
    # depends_on:
    #   db:
    #     condition: service_healthy

  # db servisini tamamen kaldırın veya comment out yapın
  # db:
  #   ...
```

---

### 9️⃣ Test ve Doğrulama

**Sunucuda bağlantıyı test edin:**

```bash
# PostgreSQL'e bağlanın
psql -h localhost -U app -d teknik_servis

# VEYA remote'tan
psql -h YOUR_DB_SERVER_IP -U app -d teknik_servis

# Tabloları kontrol edin
\dt

# Kullanıcıları kontrol edin
SELECT * FROM users;

# Çıkış
\q
```

**Uygulama testi:**

```bash
# API health check
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs
```

---

### 🔟 Eski Docker DB'yi Durdurma (Opsiyonel)

**Eğer artık Docker DB'ye ihtiyacınız yoksa:**

```bash
# Development'ta Docker DB'yi durdurun
docker-compose stop db
docker-compose rm db

# VEYA sadece durdurun (verileri korumak için)
docker-compose stop db
```

---

## ✅ Kontrol Listesi

- [ ] Docker DB'den dump alındı
- [ ] Sunucuda PostgreSQL kuruldu
- [ ] Kullanıcı (app) ve veritabanı (teknik_servis) oluşturuldu
- [ ] Backup restore edildi
- [ ] Remote erişim yapılandırıldı (gerekirse)
- [ ] Firewall kuralları eklendi
- [ ] Migration'lar çalıştırıldı
- [ ] Environment variables güncellendi
- [ ] Docker compose güncellendi
- [ ] Bağlantı test edildi
- [ ] Uygulama test edildi

---

## 🔒 Güvenlik Notları

1. **Şifre Değiştirme (Production için önerilir):**
   ```sql
   ALTER USER app WITH PASSWORD 'yeni_güçlü_şifre';
   ```

2. **SSL Bağlantısı:**
   ```env
   DATABASE_URL=postgresql://app:password@host:5432/teknik_servis?sslmode=require
   ```

3. **IP Whitelisting:**
   - Sadece uygulama sunucusu IP'sinden erişime izin verin
   - `pg_hba.conf` dosyasında sadece gerekli IP'leri ekleyin

4. **Firewall:**
   - PostgreSQL port'unu (5432) sadece gerekli IP'lerden açın
   - Public internet'ten erişimi kapatın (VPN veya private network kullanın)

---

## 🐛 Troubleshooting

### Connection Refused
```bash
# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql

# Port dinleniyor mu?
sudo netstat -tlnp | grep 5432

# Firewall kontrolü
sudo ufw status
```

### Authentication Failed
```bash
# Kullanıcı var mı?
sudo -u postgres psql -c "\du"

# Şifre doğru mu?
# pg_hba.conf'da md5 yerine trust kullanmayın (güvenlik riski)
```

### Permission Denied
```bash
# Kullanıcıya yetki verin
sudo -u postgres psql -d teknik_servis -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;"
sudo -u postgres psql -d teknik_servis -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app;"
```

---

## 📝 Hızlı Komut Özeti

```bash
# 1. Dump al
docker-compose exec db pg_dump -U app -d teknik_servis > backup.sql

# 2. Sunucuya yükle
scp backup.sql user@server:/tmp/

# 3. Sunucuda restore et
ssh user@server
sudo -u postgres psql -d teknik_servis < /tmp/backup.sql

# 4. Test et
psql -h localhost -U app -d teknik_servis -c "SELECT COUNT(*) FROM users;"
```
