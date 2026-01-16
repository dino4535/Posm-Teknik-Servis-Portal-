from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    entity_type = Column(String(50), nullable=False)  # Request, User, POSM, etc.
    entity_id = Column(Integer, nullable=True)  # ID of the affected entity
    old_values = Column(JSON, nullable=True)  # Previous values (for updates)
    new_values = Column(JSON, nullable=True)  # New values
    description = Column(Text, nullable=True)  # Human-readable description
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="audit_logs")
