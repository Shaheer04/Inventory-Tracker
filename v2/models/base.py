from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class TimestampMixin():
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)