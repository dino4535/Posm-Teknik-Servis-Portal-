from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Rapor adı
    report_type = Column(String(50), nullable=False)  # 'weekly_completed', 'pending_requests', 'custom'
    cron_expression = Column(String(100), nullable=False)  # Cron format: "day_of_week hour minute"
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Depo bazlı filtreleme
    depot_ids = Column(JSON, nullable=True)  # [1, 2, 3] veya null (tüm depolar)
    
    # Alıcı kullanıcılar
    recipient_user_ids = Column(JSON, nullable=False)  # [1, 2, 3] - Hangi kullanıcılara gönderilecek
    
    # Ek filtreler
    status_filter = Column(JSON, nullable=True)  # ['Beklemede', 'Tamamlandı'] veya null
    job_type_filter = Column(JSON, nullable=True)  # ['Montaj', 'Demontaj'] veya null
    
    # Özel sorgu parametreleri
    custom_params = Column(JSON, nullable=True)  # Ek parametreler
    
    # Zamanlama bilgileri
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_by = relationship("User", foreign_keys=[created_by_user_id])
