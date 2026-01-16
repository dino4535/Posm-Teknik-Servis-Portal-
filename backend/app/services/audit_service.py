from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse, AuditLogFilter


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Yeni audit log kaydı oluştur"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs(
        self,
        filter_params: Optional[AuditLogFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogResponse]:
        """Audit logları getir (filtreleme ile)"""
        query = self.db.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)

        if filter_params:
            if filter_params.user_id:
                query = query.filter(AuditLog.user_id == filter_params.user_id)
            if filter_params.action:
                query = query.filter(AuditLog.action == filter_params.action)
            if filter_params.entity_type:
                query = query.filter(AuditLog.entity_type == filter_params.entity_type)
            if filter_params.entity_id:
                query = query.filter(AuditLog.entity_id == filter_params.entity_id)
            if filter_params.start_date:
                query = query.filter(AuditLog.created_at >= filter_params.start_date)
            if filter_params.end_date:
                query = query.filter(AuditLog.created_at <= filter_params.end_date)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()

        result = []
        for log in logs:
            user_name = None
            user_email = None
            if log.user:
                user_name = log.user.name
                user_email = log.user.email

            result.append(AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                user_name=user_name,
                user_email=user_email,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                old_values=log.old_values,
                new_values=log.new_values,
                description=log.description,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at
            ))

        return result

    def get_log_count(self, filter_params: Optional[AuditLogFilter] = None) -> int:
        """Filtrelenmiş log sayısını getir"""
        query = self.db.query(AuditLog)

        if filter_params:
            if filter_params.user_id:
                query = query.filter(AuditLog.user_id == filter_params.user_id)
            if filter_params.action:
                query = query.filter(AuditLog.action == filter_params.action)
            if filter_params.entity_type:
                query = query.filter(AuditLog.entity_type == filter_params.entity_type)
            if filter_params.entity_id:
                query = query.filter(AuditLog.entity_id == filter_params.entity_id)
            if filter_params.start_date:
                query = query.filter(AuditLog.created_at >= filter_params.start_date)
            if filter_params.end_date:
                query = query.filter(AuditLog.created_at <= filter_params.end_date)

        return query.count()
