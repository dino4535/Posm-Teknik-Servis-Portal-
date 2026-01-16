from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    user_email: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
