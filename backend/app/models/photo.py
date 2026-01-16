from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    path_or_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    request = relationship("Request", backref="photos")
