from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class JobType(str, enum.Enum):
    MONTAJ = "Montaj"
    DEMONTAJ = "Demontaj"
    BAKIM = "Bakım"


class RequestStatus(str, enum.Enum):
    BEKLEMEDE = "Beklemede"
    TAKVIME_EKLENDI = "TakvimeEklendi"
    TAMAMLANDI = "Tamamlandı"
    IPTAL = "İptal"


class RequestPriority(str, enum.Enum):
    DUSUK = "Düşük"
    ORTA = "Orta"
    YUKSEK = "Yüksek"
    ACIL = "Acil"


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=False)
    territory_id = Column(Integer, ForeignKey("territories.id"), nullable=True)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)
    current_posm = Column(String, nullable=True)
    job_type = Column(String(20), nullable=False)
    job_detail = Column(Text, nullable=True)
    request_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    requested_date = Column(Date, nullable=False)
    planned_date = Column(Date, nullable=True)
    posm_id = Column(Integer, ForeignKey("posm.id"), nullable=True)
    status = Column(String(20), default=RequestStatus.BEKLEMEDE.value, nullable=False)
    priority = Column(String(20), default=RequestPriority.ORTA.value, nullable=False)
    job_done_desc = Column(Text, nullable=True)
    completed_date = Column(Date, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="requests")
    dealer = relationship("Dealer", backref="requests")
    territory = relationship("Territory", backref="requests")
    depot = relationship("Depot", backref="requests")
    posm = relationship("Posm", backref="requests")
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    completed_by_user = relationship("User", foreign_keys=[completed_by])
