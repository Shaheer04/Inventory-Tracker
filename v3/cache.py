from functools import wraps
import pickle
import redis
from typing import Callable


# Redis client setup
redis_client = redis.Redis(
    host="localhost",  # Change to your Redis host
    port=6379,         # Default Redis port
    db=0,              # Default Redis database
    decode_responses=False  # Keep as binary for pickle serialization
)


# Cache decorator
def cache(expire: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get data from cache
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return pickle.loads(cached_data)
            
            # If not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Store the result in cache
            redis_client.setex(
                name=cache_key,
                time=expire,
                value=pickle.dumps(result)
            )
            
            return result
        return wrapper
    return decorator