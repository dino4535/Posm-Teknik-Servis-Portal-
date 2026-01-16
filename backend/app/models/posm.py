from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Posm(Base):
    __tablename__ = "posm"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # unique kaldırıldı, depot bazında unique olacak
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)
    ready_count = Column(Integer, default=0, nullable=False)
    repair_pending_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    depot = relationship("Depot", backref="posms")
