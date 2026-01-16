from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"
    depot_id: Optional[int] = None  # Backward compatibility
    depot_ids: Optional[list[int]] = None  # Many-to-many


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    depot_id: Optional[int] = None  # Backward compatibility
    depot_ids: Optional[list[int]] = None  # Many-to-many
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    depot_ids: Optional[list[int]] = None  # Include in response
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
