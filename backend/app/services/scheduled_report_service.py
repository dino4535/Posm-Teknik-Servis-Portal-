from sqlalchemy.orm import Session
from app.models.scheduled_report import ScheduledReport
from app.models.user import User
from app.models.depot import Depot
from app.schemas.scheduled_report import ScheduledReportCreate, ScheduledReportUpdate
from typing import List, Optional
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class ScheduledReportService:
    @staticmethod
    def create_report(db: Session, report_data: ScheduledReportCreate, user_id: int) -> ScheduledReport:
        """Yeni otomatik rapor oluştur"""
        report = ScheduledReport(
            name=report_data.name,
            report_type=report_data.report_type,
            cron_expression=report_data.cron_expression,
            is_active=report_data.is_active,
            depot_ids=report_data.depot_ids,
            recipient_user_ids=report_data.recipient_user_ids,
            status_filter=report_data.status_filter,
            job_type_filter=report_data.job_type_filter,
            custom_params=report_data.custom_params,
            created_by_user_id=user_id
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_all_reports(db: Session) -> List[ScheduledReport]:
        """Tüm otomatik raporları getir"""
        return db.query(ScheduledReport).order_by(ScheduledReport.created_at.desc()).all()

    @staticmethod
    def get_report_by_id(db: Session, report_id: int) -> Optional[ScheduledReport]:
        """ID'ye göre rapor getir"""
        return db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()

    @staticmethod
    def update_report(db: Session, report_id: int, report_data: ScheduledReportUpdate) -> Optional[ScheduledReport]:
        """Raporu güncelle"""
        report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not report:
            return None
        
        update_data = report_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(report, key, value)
        
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def delete_report(db: Session, report_id: int) -> bool:
        """Raporu sil"""
        report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not report:
            return False
        
        db.delete(report)
        db.commit()
        return True

    @staticmethod
    def get_active_reports(db: Session) -> List[ScheduledReport]:
        """Aktif raporları getir"""
        return db.query(ScheduledReport).filter(ScheduledReport.is_active == True).all()

    @staticmethod
    def update_last_sent(db: Session, report_id: int):
        """Raporun son gönderim zamanını güncelle"""
        report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if report:
            report.last_sent_at = datetime.now()
            db.commit()
