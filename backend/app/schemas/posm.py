from pydantic import BaseModel
from typing import Optional


class PosmResponse(BaseModel):
    id: int
    name: str
    depot_id: Optional[int] = None
    ready_count: int
    repair_pending_count: int

    class Config:
        from_attributes = True


class PosmCreateRequest(BaseModel):
    name: str
    depot_id: int
    ready_count: int = 0
    repair_pending_count: int = 0


class PosmUpdateRequest(BaseModel):
    name: Optional[str] = None
    ready_count: Optional[int] = None
    repair_pending_count: Optional[int] = None


class PosmStockResponse(BaseModel):
    hazirAdet: int
    tamirBekleyen: int


class PosmTransferRequest(BaseModel):
    posm_id: int
    from_depot_id: int
    to_depot_id: int
    quantity: int
    transfer_type: str  # "ready" veya "repair_pending"
    notes: Optional[str] = None


class PosmTransferResponse(BaseModel):
    id: int
    posm_id: int
    from_depot_id: int
    to_depot_id: int
    quantity: int
    transfer_type: str
    notes: Optional[str] = None
    transferred_by: int
    created_at: str

    class Config:
        from_attributes = True
