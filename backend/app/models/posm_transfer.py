from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class PosmTransfer(Base):
    __tablename__ = "posm_transfers"

    id = Column(Integer, primary_key=True, index=True)
    posm_id = Column(Integer, ForeignKey("posm.id", ondelete="CASCADE"), nullable=False)
    from_depot_id = Column(Integer, ForeignKey("depots.id", ondelete="CASCADE"), nullable=False)
    to_depot_id = Column(Integer, ForeignKey("depots.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)  # Transfer edilen miktar
    transfer_type = Column(String(20), nullable=False)  # "ready" veya "repair_pending"
    notes = Column(Text, nullable=True)
    transferred_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    posm = relationship("Posm", backref="transfers")
    from_depot = relationship("Depot", foreign_keys=[from_depot_id], backref="outgoing_transfers")
    to_depot = relationship("Depot", foreign_keys=[to_depot_id], backref="incoming_transfers")
    transferred_by_user = relationship("User", foreign_keys=[transferred_by])
