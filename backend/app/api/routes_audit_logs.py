from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.schemas.audit_log import AuditLogResponse, AuditLogFilter
from pydantic import BaseModel
from typing import List

router = APIRouter()


def require_admin(current_user: dict = Depends(AuthService.get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Audit logları getir"""
    filter_params = AuditLogFilter(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date
    )

    audit_service = AuditService(db)
    logs = audit_service.get_logs(filter_params, limit=limit, offset=offset)
    total = audit_service.get_log_count(filter_params)

    return AuditLogListResponse(
        logs=logs,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/stats")
async def get_audit_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Audit log istatistikleri"""
    from sqlalchemy import func
    from app.models.audit_log import AuditLog

    query = db.query(AuditLog)

    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    # Action bazında sayılar
    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()

    # Entity type bazında sayılar
    entity_stats = db.query(
        AuditLog.entity_type,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.entity_type).all()

    # Kullanıcı bazında sayılar
    user_stats = db.query(
        AuditLog.user_id,
        func.count(AuditLog.id).label('count')
    ).filter(AuditLog.user_id.isnot(None)).group_by(AuditLog.user_id).all()

    return {
        "by_action": {action: count for action, count in action_stats},
        "by_entity": {entity: count for entity, count in entity_stats},
        "by_user": {user_id: count for user_id, count in user_stats},
        "total": query.count()
    }
