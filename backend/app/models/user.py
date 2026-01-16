from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

# Many-to-many junction table for user-depot relationship
user_depots = Table(
    'user_depots',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('depot_id', Integer, ForeignKey('depots.id', ondelete='CASCADE'), primary_key=True)
)


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    TECH = "tech"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)  # Backward compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    depot = relationship("Depot", foreign_keys=[depot_id], backref="users_legacy")  # Backward compatibility
    depots = relationship("Depot", secondary=user_depots, backref="users")  # Many-to-many
