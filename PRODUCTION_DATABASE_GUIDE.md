# 🗄️ Production Database Yönetim Rehberi

## 📋 Seçenekler

Production'da veritabanını yönetmek için birkaç seçenek var. Her birinin avantaj ve dezavantajları:

---

## 1️⃣ Docker Compose ile (Basit, Küçük Projeler)

### ✅ Avantajlar
- Hızlı kurulum
- Tek komutla başlatma
- Backup kolay (volume'lar)
- Düşük maliyet

### ❌ Dezavantajlar
- Tek sunucu bağımlılığı
- Yüksek kullanılabilirlik yok
- Otomatik scaling yok
- Yönetim sizin sorumluluğunuzda

### Kullanım

```bash
# Production docker-compose ile
docker-compose -f docker-compose.production.yml up -d

# Backup
docker-compose exec db pg_dump -U app teknik_servis > backup.sql

# Restore
docker-compose exec -T db psql -U app -d teknik_servis < backup.sql
```

### Environment Variables (.env.production)

```env
DATABASE_URL=postgresql://app:secure_password@db:5432/teknik_servis
DB_USER=app
DB_PASSWORD=very_secure_password_here
DB_NAME=teknik_servis
DB_PORT=5432
```

---

## 2️⃣ Managed PostgreSQL Servisleri (ÖNERİLEN) ⭐

### ✅ Avantajlar
- Otomatik backup
- Yüksek kullanılabilirlik (HA)
- Otomatik scaling
- Güvenlik yamaları otomatik
- Monitoring ve alerting
- Point-in-time recovery
- Read replicas

### ❌ Dezavantajlar
- Aylık maliyet ($10-100+)
- Vendor lock-in riski

### Popüler Seçenekler

#### A. AWS RDS PostgreSQL
```env
DATABASE_URL=postgresql://username:password@your-db.region.rds.amazonaws.com:5432/teknik_servis
```

**Özellikler:**
- Multi-AZ deployment (yüksek kullanılabilirlik)
- Automated backups
- Read replicas
- Encryption at rest
- VPC isolation

**Maliyet:** ~$15-50/ay (db.t3.micro - db.t3.medium)

#### B. DigitalOcean Managed Databases
```env
DATABASE_URL=postgresql://username:password@your-db-do-user-123456.db.ondigitalocean.com:25060/teknik_servis?sslmode=require
```

**Özellikler:**
- Basit kurulum
- Otomatik backup
- Standby nodes
- Connection pooling

**Maliyet:** ~$15-60/ay

#### C. Azure Database for PostgreSQL
```env
DATABASE_URL=postgresql://username:password@your-server.postgres.database.azure.com:5432/teknik_servis
```

**Özellikler:**
- Flexible server
- High availability
- Automated backups
- Azure integration

**Maliyet:** ~$25-100/ay

#### D. Google Cloud SQL
```env
DATABASE_URL=postgresql://username:password@your-ip:5432/teknik_servis
```

**Özellikler:**
- Automatic failover
- Read replicas
- Point-in-time recovery
- Cloud integration

**Maliyet:** ~$20-80/ay

#### E. Supabase / Neon / Railway (Modern Alternatifler)
```env
# Supabase
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# Neon (Serverless PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxx.region.neon.tech/neondb

# Railway
DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:5432/railway
```

**Özellikler:**
- Kolay kurulum
- Düşük maliyet
- Modern tooling
- Serverless (Neon)

**Maliyet:** ~$5-25/ay

---

## 3️⃣ Ayrı PostgreSQL Sunucusu (VPS/Dedicated)

### ✅ Avantajlar
- Tam kontrol
- Özelleştirilebilir
- Düşük maliyet (küçük projeler için)

### ❌ Dezavantajlar
- Yönetim sizin sorumluluğunuzda
- Backup stratejisi sizde
- Güvenlik yamaları sizde
- Scaling manuel

### Kurulum Örneği (Ubuntu/Debian)

```bash
# PostgreSQL kurulumu
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16

# Veritabanı oluştur
sudo -u postgres psql
CREATE DATABASE teknik_servis;
CREATE USER app WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE teknik_servis TO app;
\q

# Remote erişim için (opsiyonel)
sudo nano /etc/postgresql/16/main/postgresql.conf
# listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# host    teknik_servis    app    0.0.0.0/0    md5
```

### Environment Variables

```env
DATABASE_URL=postgresql://app:password@your-server-ip:5432/teknik_servis
```

---

## 4️⃣ Kubernetes (Büyük Ölçekli Projeler)

### ✅ Avantajlar
- Otomatik scaling
- Yüksek kullanılabilirlik
- Self-healing
- Service mesh entegrasyonu

### ❌ Dezavantajlar
- Karmaşık kurulum
- Yönetim zorluğu
- Yüksek maliyet

### Örnek: PostgreSQL Operator (Crunchy Data)

```yaml
apiVersion: postgres-operator.crunchydata.com/v1beta1
kind: PostgresCluster
metadata:
  name: teknik-servis-db
spec:
  image: registry.developers.crunchydata.com/crunchydata/crunchy-postgres:ubi8-16.0-1
  postgresVersion: 16
  instances:
    - name: instance1
      replicas: 2
      dataVolumeClaimSpec:
        accessModes:
        - "ReadWriteOnce"
        resources:
          requests:
            storage: 10Gi
```

---

## 🔄 Migration Stratejisi (Development → Production)

### 1. Veri Migrasyonu

```bash
# Development'tan dump al
docker-compose exec db pg_dump -U app teknik_servis > backup.sql

# Production'a yükle
# Managed DB için:
psql -h your-db-host -U app -d teknik_servis < backup.sql

# Docker için:
docker-compose -f docker-compose.production.yml exec -T db psql -U app -d teknik_servis < backup.sql
```

### 2. Schema Migration

```bash
# Alembic migration'ları çalıştır
docker-compose exec api alembic upgrade head

# Production'da:
docker-compose -f docker-compose.production.yml exec api alembic upgrade head
```

### 3. Environment Variables Güncelleme

```env
# .env.production
DATABASE_URL=postgresql://app:password@production-db-host:5432/teknik_servis
DB_USER=app
DB_PASSWORD=secure_production_password
DB_NAME=teknik_servis
```

---

## 🔒 Production Güvenlik Checklist

- [ ] Güçlü şifre kullanın (min 16 karakter, özel karakterler)
- [ ] SSL/TLS bağlantısı zorunlu (`sslmode=require`)
- [ ] Firewall kuralları (sadece gerekli IP'lerden erişim)
- [ ] Regular backup (günlük)
- [ ] Backup encryption
- [ ] Database user'ları minimum yetki ile oluşturun
- [ ] Connection pooling kullanın
- [ ] SQL injection koruması (SQLAlchemy ORM)
- [ ] Audit logging aktif
- [ ] Regular security updates

---

## 📊 Backup Stratejisi

### Otomatik Backup (Cron Job)

```bash
# /etc/cron.daily/db-backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
docker-compose exec -T db pg_dump -U app teknik_servis | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Eski backup'ları sil (30 günden eski)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Managed DB Backup

Çoğu managed database servisi otomatik backup sağlar:
- **AWS RDS:** Automated backups (7-35 gün retention)
- **DigitalOcean:** Daily backups (7 gün retention)
- **Azure:** Automated backups (7-35 gün retention)

---

## 🎯 Öneri: Hangi Seçeneği Kullanmalıyım?

### Küçük Proje (< 1000 kullanıcı)
→ **Docker Compose** veya **Supabase/Neon**

### Orta Ölçekli Proje (1000-10000 kullanıcı)
→ **DigitalOcean Managed DB** veya **AWS RDS (db.t3.small)**

### Büyük Ölçekli Proje (> 10000 kullanıcı)
→ **AWS RDS Multi-AZ** veya **Kubernetes**

### Startup / MVP
→ **Supabase** veya **Neon** (düşük maliyet, kolay kurulum)

---

## 📝 Örnek: DigitalOcean Managed Database Kurulumu

1. **DigitalOcean Dashboard'a girin**
2. **Databases → Create Database → PostgreSQL 16**
3. **Plan seçin** (Basic, $15/ay başlangıç için)
4. **Database oluşturun**
5. **Connection string'i alın:**

```env
DATABASE_URL=postgresql://doadmin:password@db-xxx-do-user-123456-0.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

6. **.env.production dosyasını güncelleyin:**

```env
DATABASE_URL=postgresql://doadmin:password@db-xxx-do-user-123456-0.db.ondigitalocean.com:25060/teknik_servis?sslmode=require
DB_USER=doadmin
DB_PASSWORD=your_password
DB_NAME=teknik_servis
```

7. **docker-compose.production.yml'de DB servisini kaldırın** (managed DB kullanıyorsanız)

8. **Migration'ları çalıştırın:**

```bash
docker-compose -f docker-compose.production.yml exec api alembic upgrade head
```

---

## 🔧 Troubleshooting

### Connection Timeout
- Firewall kurallarını kontrol edin
- IP whitelist'e ekleyin (managed DB için)
- SSL mode'u kontrol edin

### Authentication Failed
- Şifre doğru mu?
- User yetkileri var mı?
- Host-based authentication (pg_hba.conf) kontrol edin

### Database Not Found
- Veritabanı oluşturuldu mu?
- Connection string'de database adı doğru mu?

---

## 📚 Kaynaklar

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [DigitalOcean Managed Databases](https://docs.digitalocean.com/products/databases/)
- [Supabase Documentation](https://supabase.com/docs)
