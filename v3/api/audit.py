# api/audit_logs_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from models import AuditLog, User
from database import get_read_session
from core.security import get_api_key
from typing import List, Optional
from datetime import datetime
from cache import cache

router = APIRouter()

@router.get("/", response_model=List[AuditLog])
@cache(expire=30)  # Short cache time for audit logs
async def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_read_session),
    current_user: User = Depends(get_api_key)
):
    """
    Get audit logs with optional filters.
    Only admin users can access all logs.
    """
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin users can access audit logs")
    
    # Build query
    query = select(AuditLog)
    
    # Apply filters
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if from_date:
        query = query.where(AuditLog.timestamp >= from_date)
    
    if to_date:
        query = query.where(AuditLog.timestamp <= to_date)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    results = session.exec(query).all()
    
    return results