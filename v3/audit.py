# audit.py
from fastapi import Request, Depends
from sqlmodel import Session
from models import AuditLog, User
from database import get_write_session
from typing import Optional, Dict, Any, Union
import json
from datetime import datetime
import asyncio
from functools import wraps

def log_audit(
    action: str,
    resource_type: str,
    resource_id: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    user: Optional[User] = None,
    session: Optional[Session] = None
):
    """Create an audit log entry"""
    # Convert dictionaries to JSON strings
    old_values_json = json.dumps(old_values) if old_values else None
    new_values_json = json.dumps(new_values) if new_values else None
    
    # Create audit log entry
    log_entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "system",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values_json,
        new_values=new_values_json,
        timestamp=datetime.now()
    )
    
    # If session is provided, use it, otherwise create a new one
    if session:
        session.add(log_entry)
    else:
        with Session(get_write_session()) as new_session:
            new_session.add(log_entry)
            new_session.commit()
    
    return log_entry

# Decorator for auditing database operations
def audit_operation(action: str, resource_type: str):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get request object from kwargs
            request = next((kwargs[key] for key in kwargs if isinstance(kwargs[key], Request)), None)
            
            # Get user from kwargs
            user = next((kwargs[key] for key in kwargs if hasattr(kwargs[key], 'username') and 
                         hasattr(kwargs[key], 'id')), None)
            
            # Get session from kwargs
            session = next((kwargs[key] for key in kwargs if isinstance(kwargs[key], Session)), None)
            
            # Get IP address
            ip_address = request.client.host if request else None
            
            # Extract resource ID from function arguments
            # This is a simplification; in practice, you might need to extract it differently
            resource_id = kwargs.get('id') or args[0] if args else None
            
            # For UPDATE operations, get old values
            old_values = None
            if action == "UPDATE" and resource_id and session:
                # Get the model class from resource_type
                model_class = globals().get(resource_type)
                if model_class:
                    old_resource = session.get(model_class, resource_id)
                    if old_resource:
                        old_values = {k: v for k, v in old_resource.dict().items() 
                                     if k not in ['id', 'created_at', 'updated_at']}
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # For CREATE operations, get new values from the result
            new_values = None
            if result:
                if action == "CREATE":
                    if hasattr(result, 'dict'):
                        new_values = {k: v for k, v in result.dict().items() 
                                     if k not in ['id', 'created_at', 'updated_at']}
                        resource_id = result.id
                elif action == "UPDATE" and hasattr(result, 'dict'):
                    new_values = {k: v for k, v in result.dict().items() 
                                 if k not in ['id', 'created_at', 'updated_at']}
            
            # Log the operation
            log_audit(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                user=user,
                session=session
            )
            
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for synchronous functions
            # Get request object from kwargs
            request = next((kwargs[key] for key in kwargs if isinstance(kwargs[key], Request)), None)
            
            # Get user from kwargs
            user = next((kwargs[key] for key in kwargs if hasattr(kwargs[key], 'username') and 
                         hasattr(kwargs[key], 'id')), None)
            
            # Get session from kwargs
            session = next((kwargs[key] for key in kwargs if isinstance(kwargs[key], Session)), None)
            
            # Extract resource ID from function arguments
            resource_id = kwargs.get('id') or args[0] if args else None
            
            # For UPDATE operations, get old values
            old_values = None
            if action == "UPDATE" and resource_id and session:
                # Get the model class from resource_type
                model_class = globals().get(resource_type)
                if model_class:
                    old_resource = session.get(model_class, resource_id)
                    if old_resource:
                        old_values = {k: v for k, v in old_resource.dict().items() 
                                     if k not in ['id', 'created_at', 'updated_at']}
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # For CREATE operations, get new values from the result
            new_values = None
            if result:
                if action == "CREATE":
                    if hasattr(result, 'dict'):
                        new_values = {k: v for k, v in result.dict().items() 
                                     if k not in ['id', 'created_at', 'updated_at']}
                        resource_id = result.id
                elif action == "UPDATE" and hasattr(result, 'dict'):
                    new_values = {k: v for k, v in result.dict().items() 
                                 if k not in ['id', 'created_at', 'updated_at']}
            
            # Log the operation
            log_audit(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                user=user,
                session=session
            )
            
            return result
        
        # Return appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
            
    return decorator