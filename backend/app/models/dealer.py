from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base


class Dealer(Base):
    __tablename__ = "dealers"

    id = Column(Integer, primary_key=True, index=True)
    territory_id = Column(Integer, ForeignKey("territories.id"), nullable=True)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)
    code = Column(String, nullable=False, index=True)  # unique kaldırıldı, depot bazında unique olacak
    name = Column(String, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    territory = relationship("Territory", backref="dealers")
    depot = relationship("Depot", backref="dealers")
