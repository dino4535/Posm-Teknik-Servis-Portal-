from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class RequestCreate(BaseModel):
    territory_id: Optional[int] = None
    dealer_id: Optional[int] = None
    dealer_code: Optional[str] = None  # Frontend'den gelecek, backend'de dealer_id'ye çevrilecek
    current_posm: Optional[str] = None
    job_type: str  # Montaj, Demontaj, Bakım
    job_detail: Optional[str] = None
    requested_date: date
    planned_date: Optional[date] = None
    posm_id: Optional[int] = None
    priority: Optional[str] = "Orta"  # Düşük, Orta, Yüksek, Acil


class RequestResponse(BaseModel):
    id: int
    territory: Optional[str] = None
    bayiKodu: str
    bayiAdi: str
    mevcutPosm: Optional[str] = None
    yapilacakIs: str
    talepTarihi: str
    istenentarih: str
    posmAdi: Optional[str] = None
    planlananTarih: Optional[str] = None
    yapilanIsler: Optional[str] = None
    durum: str
    oncelik: Optional[str] = None
    kullanici: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class RequestDetailResponse(BaseModel):
    id: int
    talepTarihi: str
    planlananTarih: Optional[str] = None
    tamamlanmaTarihi: Optional[str] = None
    territory: Optional[str] = None
    bayiKodu: str
    bayiAdi: str
    yapilacakIs: str
    yapilacakIsDetay: Optional[str] = None
    posmAdi: Optional[str] = None
    durum: str
    yapilanIsler: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    photos: list = []
    tamamlayanKullanici: Optional[str] = None
    guncelleyenKullanici: Optional[str] = None


class RequestUpdate(BaseModel):
    status: Optional[str] = None
    planned_date: Optional[date] = None
    completed_date: Optional[date] = None
    job_done_desc: Optional[str] = None
    priority: Optional[str] = None


class RequestStatsResponse(BaseModel):
    open: int
    completed: int
    pending: int
