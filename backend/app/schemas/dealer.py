from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class DealerBase(BaseModel):
    territory_id: Optional[int] = None
    depot_id: Optional[int] = None
    code: str
    name: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class DealerCreate(DealerBase):
    pass


class DealerUpdate(BaseModel):
    territory_id: Optional[int] = None
    depot_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class DealerResponse(BaseModel):
    id: int
    territory_id: Optional[int]
    depot_id: Optional[int]
    code: str
    name: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]

    class Config:
        from_attributes = True


class DealerSearchResponse(BaseModel):
    territory: Optional[str]
    bayiKodu: str
    bayiAdi: str

    class Config:
        from_attributes = True
