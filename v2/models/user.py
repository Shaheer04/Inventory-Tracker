from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from .base import TimestampMixin
import secrets

class User(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), unique=True, index=True)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    
    # Relationships
    movements: List["StockMovement"] = Relationship(back_populates="user")