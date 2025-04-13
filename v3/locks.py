from cache import redis_client
import secrets
from typing import Tuple

async def acquire_lock(resource_key: str, lock_ttl: int = 30) -> Tuple[bool, str, str]:
    """
    Acquire a distributed lock using Redis
    
    Args:
        resource_key: The resource to lock
        lock_ttl: Time-to-live for the lock in seconds
        
    Returns:
        Tuple of (acquired, lock_id, lock_key)
    """
    lock_key = f"lock:{resource_key}"
    lock_id = secrets.token_hex(8)
    
    # Try to acquire the lock
    acquired = redis_client.set(lock_key, lock_id, nx=True, ex=lock_ttl)
    
    return acquired, lock_id, lock_key

async def release_lock(lock_key: str, lock_id: str) -> bool:
    """
    Release a distributed lock using Redis
    
    Args:
        lock_key: The lock key to release
        lock_id: The lock ID to verify ownership
        
    Returns:
        True if lock was released, False otherwise
    """
    # Only release if we own the lock
    current_id = redis_client.get(lock_key)
    if current_id and current_id.decode() == lock_id:
        redis_client.delete(lock_key)
        return True
    return False

# Initialize locks on import
def init_locks():
    redis_client.set("lock:initialized", "true")