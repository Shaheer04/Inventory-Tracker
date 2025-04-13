from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime   
from base import TimestampMixin
from typing import Optional, List

class Supplier(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    contact_info: Optional[str] = None
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # Relationships
    supply_records: List["SupplyRecord"] = Relationship(back_populates="supplier")
    stores: List["Store"] = Relationship(back_populates="suppliers", link_model="StoreSupplierLink")

class SupplyRecord(SQLModel, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id")
    product_id: int = Field(foreign_key="product.id")
    store_id: int = Field(foreign_key="store.id")
    purchase_price: float
    quantity: float
    order_date: datetime = Field(default_factory=datetime.utcnow)
    delivery_date: Optional[datetime] = None
    order_reference: str = Field(index=True)
    status: str = Field(default="ordered")  # ordered, delivered, cancelled
    
    # Relationships
    supplier: Supplier = Relationship(back_populates="supply_records")
    product: "Product" = Relationship(back_populates="supply_records")
    store: "Store" = Relationship(back_populates="supply_records")

class StoreSupplierLink(SQLModel, table=True):
    store_id: int = Field(foreign_key="store.id", primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", primary_key=True)