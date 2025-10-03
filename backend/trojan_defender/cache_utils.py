"""
Cache utilities for Trojan Defender application.
Provides decorators and utilities for efficient caching.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union

from django.core.cache import cache, caches
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse
from django.utils.cache import get_cache_key
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

logger = logging.getLogger(__name__)


def cache_key_generator(*args, **kwargs) -> str:
    """
    Generate a consistent cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Generated cache key
    """
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    
    # Serialize to JSON for consistent ordering
    key_string = json.dumps(key_data, sort_keys=True, cls=DjangoJSONEncoder)
    
    # Create hash for consistent length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached_function(timeout: int = 300, cache_alias: str = 'default', key_prefix: str = ''):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        cache_alias: Cache backend to use
        key_prefix: Prefix for cache keys
        
    Usage:
        @cached_function(timeout=3600, key_prefix='user_data')
        def get_user_profile(user_id):
            return expensive_database_query(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            cache_key_base = cache_key_generator(func_name, *args, **kwargs)
            cache_key = f"{key_prefix}:{cache_key_base}" if key_prefix else cache_key_base
            
            # Get cache backend
            cache_backend = caches[cache_alias]
            
            # Try to get from cache
            try:
                cached_result = cache_backend.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get failed for key {cache_key}: {e}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache_backend.set(cache_key, result, timeout)
                logger.debug(f"Cached result for key: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Function execution failed: {e}")
                raise
                
        return wrapper
    return decorator


def cached_view(timeout: int = 300, cache_alias: str = 'default', vary_on: Optional[list] = None):
    """
    Decorator to cache view responses.
    
    Args:
        timeout: Cache timeout in seconds
        cache_alias: Cache backend to use
        vary_on: List of headers to vary cache on
        
    Usage:
        @cached_view(timeout=3600, vary_on=['User-Agent'])
        def my_view(request):
            return render(request, 'template.html', context)
    """
    def decorator(view_func: Callable) -> Callable:
        # Apply vary_on_headers if specified
        if vary_on:
            view_func = vary_on_headers(*vary_on)(view_func)
        
        # Apply cache_page decorator
        return cache_page(timeout, cache=cache_alias)(view_func)
    
    return decorator


class CacheManager:
    """
    Utility class for managing cache operations.
    """
    
    def __init__(self, cache_alias: str = 'default'):
        self.cache = caches[cache_alias]
        self.cache_alias = cache_alias
    
    def get_or_set(self, key: str, callable_or_value: Union[Callable, Any], 
                   timeout: int = 300, version: Optional[int] = None) -> Any:
        """
        Get value from cache or set it if not exists.
        
        Args:
            key: Cache key
            callable_or_value: Function to call or value to set if cache miss
            timeout: Cache timeout in seconds
            version: Cache version
            
        Returns:
            Cached or computed value
        """
        try:
            value = self.cache.get(key, version=version)
            if value is not None:
                return value
            
            # Compute value
            if callable(callable_or_value):
                value = callable_or_value()
            else:
                value = callable_or_value
            
            # Set in cache
            self.cache.set(key, value, timeout, version=version)
            return value
            
        except Exception as e:
            logger.error(f"Cache operation failed for key {key}: {e}")
            # Return computed value without caching
            if callable(callable_or_value):
                return callable_or_value()
            return callable_or_value
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        try:
            if hasattr(self.cache, 'delete_pattern'):
                return self.cache.delete_pattern(pattern)
            else:
                # Fallback for cache backends that don't support pattern deletion
                logger.warning(f"Cache backend {self.cache_alias} doesn't support pattern deletion")
                return 0
        except Exception as e:
            logger.error(f"Pattern deletion failed for pattern {pattern}: {e}")
            return 0
    
    def clear_cache(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics if available.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            if hasattr(self.cache, 'get_stats'):
                return self.cache.get_stats()
            else:
                return {'error': 'Statistics not available for this cache backend'}
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}


# Pre-configured cache managers
default_cache = CacheManager('default')
session_cache = CacheManager('sessions')
rate_limit_cache = CacheManager('rate_limit')


def invalidate_user_cache(user_id: int) -> None:
    """
    Invalidate all cache entries for a specific user.
    
    Args:
        user_id: User ID to invalidate cache for
    """
    patterns = [
        f"user:{user_id}:*",
        f"profile:{user_id}:*",
        f"permissions:{user_id}:*",
    ]
    
    for pattern in patterns:
        default_cache.delete_pattern(pattern)
        logger.info(f"Invalidated cache pattern: {pattern}")


def warm_cache(cache_key: str, callable_func: Callable, timeout: int = 300) -> None:
    """
    Warm up cache with pre-computed values.
    
    Args:
        cache_key: Key to store the value under
        callable_func: Function to call to get the value
        timeout: Cache timeout in seconds
    """
    try:
        value = callable_func()
        default_cache.cache.set(cache_key, value, timeout)
        logger.info(f"Warmed cache for key: {cache_key}")
    except Exception as e:
        logger.error(f"Cache warming failed for key {cache_key}: {e}")


# Cache decorators for common use cases
def cache_user_data(timeout: int = 3600):
    """Cache user-related data for 1 hour by default."""
    return cached_function(timeout=timeout, key_prefix='user_data')


def cache_threat_data(timeout: int = 1800):
    """Cache threat intelligence data for 30 minutes by default."""
    return cached_function(timeout=timeout, key_prefix='threat_data')


def cache_scan_results(timeout: int = 7200):
    """Cache scan results for 2 hours by default."""
    return cached_function(timeout=timeout, key_prefix='scan_results')


def cache_api_response(timeout: int = 600):
    """Cache API responses for 10 minutes by default."""
    return cached_view(timeout=timeout, vary_on=['Authorization', 'Accept'])