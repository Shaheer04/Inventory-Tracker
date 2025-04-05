from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from .base import TimestampMixin

class Store(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    location: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # Relationships
    stock_items: List["StoreStock"] = Relationship(back_populates="store")
    movements: List["StockMovement"] = Relationship(back_populates="store")