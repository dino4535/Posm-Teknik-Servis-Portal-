from pydantic import BaseModel
from typing import List
from datetime import date


class PlanRequestsRequest(BaseModel):
    request_ids: List[int]
    planned_date: date
