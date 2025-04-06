from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
import secrets
from models import User
from database import get_read_session, get_write_session
from core.security import get_password_hash, get_api_key, check_admin_permission
from cache import cache
from audit import audit_operation

router = APIRouter()

@router.get("/", response_model=List[User])
@cache(expire=60)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_read_session),
    current_user: User = Depends(check_admin_permission)  # Admin only
):
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    # Don't expose API keys in the response
    for user in users:
        user.api_key = "***"
    return users

@router.post("/", response_model=User)
@audit_operation(action="CREATE", resource_type = "User")
def create_user(
    username: str,
    email: str,
    password: str,
    is_admin: bool = False,
    session: Session = Depends(get_write_session),
    current_user: User = Depends(check_admin_permission)  # Admin only
):
    # Check if username or email already exists
    db_user = session.exec(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    # Create new user with API key
    api_key = secrets.token_urlsafe(32)
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        api_key=api_key,
        is_active=True,
        is_admin=is_admin
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Return user with API key visible only on creation
    return new_user

@router.get("/me", response_model=dict)
@cache(expire=60)
def read_users_me(current_user: User = Depends(get_api_key)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.post("/reset-api-key", response_model=dict)
def reset_api_key(
    user_id: int,
    session: Session = Depends(get_write_session),
    current_user: User = Depends(check_admin_permission)  # Admin only
):
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to reset another user's API key"
        )
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new API key
    new_api_key = secrets.token_urlsafe(32)
    user.api_key = new_api_key
    session.add(user)
    session.commit()
    
    return {"message": "API key reset successfully", "api_key": new_api_key}