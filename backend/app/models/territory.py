from sqlalchemy import Column, Integer, String
from app.db.base import Base


class Territory(Base):
    __tablename__ = "territories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
