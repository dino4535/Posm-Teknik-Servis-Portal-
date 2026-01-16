from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScheduledReportCreate(BaseModel):
    name: str
    report_type: str  # 'weekly_completed', 'pending_requests', 'custom'
    cron_expression: str  # "day_of_week hour minute" formatında
    is_active: bool = True
    depot_ids: Optional[List[int]] = None
    recipient_user_ids: List[int]
    status_filter: Optional[List[str]] = None
    job_type_filter: Optional[List[str]] = None
    custom_params: Optional[Dict[str, Any]] = None


class ScheduledReportUpdate(BaseModel):
    name: Optional[str] = None
    report_type: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    depot_ids: Optional[List[int]] = None
    recipient_user_ids: Optional[List[int]] = None
    status_filter: Optional[List[str]] = None
    job_type_filter: Optional[List[str]] = None
    custom_params: Optional[Dict[str, Any]] = None


class ScheduledReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    cron_expression: str
    is_active: bool
    depot_ids: Optional[List[int]]
    recipient_user_ids: List[int]
    status_filter: Optional[List[str]]
    job_type_filter: Optional[List[str]]
    custom_params: Optional[Dict[str, Any]]
    last_sent_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int]
    
    class Config:
        from_attributes = True
