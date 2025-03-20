import time
import functools
from typing import Dict, Any, Callable, Optional, Tuple

# Global cache storage
_cache: Dict[str, Tuple[Any, float, Optional[float]]] = {}

def cache_data(key: str, data: Any, ttl: Optional[float] = None) -> None:
    """
    Store data in cache with optional time-to-live in seconds.
    
    Args:
        key: Unique cache key
        data: Data to cache
        ttl: Time to live in seconds, None for no expiration
    """
    _cache[key] = (data, time.time(), ttl)

def get_cached_data(key: str) -> Optional[Any]:
    """
    Retrieve data from cache if available and not expired.
    
    Args:
        key: Cache key to lookup
        
    Returns:
        Cached data or None if not found/expired
    """
    if key not in _cache:
        return None
        
    data, timestamp, ttl = _cache[key]
    
    # Check if data has expired
    if ttl is not None and time.time() > timestamp + ttl:
        del _cache[key]
        return None
        
    return data

def invalidate_cache(key: str = None) -> None:
    """
    Remove item(s) from cache.
    
    Args:
        key: Specific key to invalidate, None to clear entire cache
    """
    global _cache
    if key is None:
        _cache = {}
    elif key in _cache:
        del _cache[key]

def cached(key_prefix: str, ttl: Optional[float] = None):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create unique key based on function name, args and kwargs
            key_parts = [key_prefix, func.__name__]
            # Add stringified args and kwargs to key
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache first
            cached_result = get_cached_data(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Calculate result and store in cache
            result = func(*args, **kwargs)
            cache_data(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
