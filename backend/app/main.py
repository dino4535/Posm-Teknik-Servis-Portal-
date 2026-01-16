from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.error_handler import error_handler_middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.api import routes_auth, routes_requests, routes_posm, routes_dealers, routes_photos, routes_territories, routes_admin, routes_work_plan, routes_reports, routes_audit_logs, routes_backup, routes_scheduled_reports
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import asyncio
import logging

# Logging yapılandırması
setup_logging()
logger = logging.getLogger(__name__)

# Scheduler'ı global olarak tanımla
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapatma işlemleri"""
    # Startup
    from app.services.scheduled_reports import send_weekly_completed_report, send_pending_requests_report, send_custom_report
    from app.db.session import SessionLocal
    from app.models.scheduled_report import ScheduledReport
    
    # Varsayılan raporları ekle (geriye dönük uyumluluk için)
    scheduler.add_job(
        send_weekly_completed_report,
        trigger=CronTrigger(day_of_week=6, hour=23, minute=59),  # Pazar = 6
        id="weekly_completed_report_default",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_pending_requests_report,
        trigger=CronTrigger(day_of_week=0, hour=6, minute=0),  # Pazartesi = 0
        id="pending_requests_report_default",
        replace_existing=True
    )
    
    # Veritabanından aktif raporları yükle ve scheduler'a ekle
    def load_scheduled_reports():
        db = SessionLocal()
        try:
            # Tablo yoksa hata vermesin
            try:
                reports = db.query(ScheduledReport).filter(ScheduledReport.is_active == True).all()
                for report in reports:
                    try:
                        # Cron expression'ı parse et: "day_of_week hour minute"
                        cron_parts = report.cron_expression.split(' ')
                        if len(cron_parts) >= 3:
                            day_of_week = int(cron_parts[0])
                            hour = int(cron_parts[1])
                            minute = int(cron_parts[2])
                            
                            # Custom report gönderme fonksiyonu
                            async def send_report_wrapper(report_id=report.id):
                                from app.db.session import SessionLocal
                                db = SessionLocal()
                                try:
                                    await send_custom_report(report_id, db)
                                finally:
                                    db.close()
                            
                            scheduler.add_job(
                                send_report_wrapper,
                                trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                                id=f"scheduled_report_{report.id}",
                                replace_existing=True
                            )
                            logger.info(f"✅ Rapor yüklendi: {report.name} (ID: {report.id})")
                    except Exception as e:
                        logger.warning(f"⚠️ Rapor yüklenemedi {report.id}: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Scheduled reports tablosu henüz oluşturulmamış: {e}")
        finally:
            db.close()
    
    # İlk yükleme
    load_scheduled_reports()
    
    scheduler.start()
    logger.info("✅ Scheduled tasks başlatıldı")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("✅ Scheduled tasks durduruldu")

app = FastAPI(
    title="Teknik Servis Portalı API",
    description="Teknik Servis ve POSM Yönetim Sistemi",
    version="1.0.0",
    lifespan=lifespan
)

# Security headers middleware (en üstte)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting middleware
if getattr(settings, 'RATE_LIMIT_ENABLED', False):
    requests_per_minute = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
    app.add_middleware(RateLimiterMiddleware, requests_per_minute=requests_per_minute)
    logger.info(f"Rate limiting aktif: {requests_per_minute} istek/dakika")

# Error handler middleware
app.middleware("http")(error_handler_middleware)

# CORS middleware - Config'den alınan origin'leri kullan
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],  # Config'den al, yoksa tüm origin'lere izin ver (geliştirme)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routes
app.include_router(routes_auth.router, prefix="/auth", tags=["Auth"])
app.include_router(routes_requests.router, prefix="/requests", tags=["Requests"])
app.include_router(routes_posm.router, prefix="/posm", tags=["POSM"])
app.include_router(routes_dealers.router, prefix="/dealers", tags=["Dealers"])
app.include_router(routes_territories.router, prefix="/territories", tags=["Territories"])
app.include_router(routes_photos.router, prefix="/photos", tags=["Photos"])
app.include_router(routes_admin.router, prefix="/admin", tags=["Admin"])
app.include_router(routes_work_plan.router, prefix="/work-plan", tags=["Work Plan"])
app.include_router(routes_reports.router, prefix="/reports", tags=["Reports"])
app.include_router(routes_audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
app.include_router(routes_backup.router, prefix="/backup", tags=["Backup"])
app.include_router(routes_scheduled_reports.router, prefix="/scheduled-reports", tags=["Scheduled Reports"])

# Static files (uploads)
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "Teknik Servis Portalı API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint - DB bağlantısını kontrol et"""
    from app.db.session import engine
    
    try:
        # DB bağlantısını test et
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e) if settings.DEBUG else "Database connection failed"
        }
