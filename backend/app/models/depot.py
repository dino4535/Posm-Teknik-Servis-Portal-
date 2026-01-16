from sqlalchemy import Column, Integer, String
from app.db.base import Base


class Depot(Base):
    __tablename__ = "depots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # MANISA, IZMIR, SALIHLI
