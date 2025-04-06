from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class AuditLog(SQLModel, table=True):
    """Model for storing audit logs of database operations"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    username: str
    action: str  # CREATE, UPDATE, DELETE
    resource_type: str  # The model name (e.g., "Product", "Store")
    resource_id: int  # ID of the affected resource
    old_values: Optional[str] = None  # JSON string of previous values
    new_values: Optional[str] = None  # JSON string of new values
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="audit_logs")