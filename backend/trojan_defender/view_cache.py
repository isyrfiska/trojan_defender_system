"""
Custom view-level caching utilities for Django REST Framework ViewSets.
Provides caching decorators that work without Django's cache middleware.
"""

import hashlib
import json
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def generate_cache_key(prefix, request, *args, **kwargs):
    """Generate a unique cache key based on request parameters."""
    # Include user ID for user-specific caching
    user_id = getattr(request.user, 'id', 'anonymous')
    
    # Include query parameters
    query_params = sorted(request.GET.items()) if hasattr(request, 'GET') else []
    
    # Include URL path parameters
    path_params = sorted(kwargs.items())
    
    # Create a unique string from all parameters
    cache_data = {
        'user_id': user_id,
        'query_params': query_params,
        'path_params': path_params,
        'method': request.method
    }
    
    # Generate hash of the cache data
    cache_string = json.dumps(cache_data, sort_keys=True)
    cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
    
    return f"{prefix}:{cache_hash}"


def cache_viewset_action(timeout=300, key_prefix=None, vary_on_user=True):
    """
    Decorator for caching DRF ViewSet actions.
    
    Args:
        timeout (int): Cache timeout in seconds (default: 5 minutes)
        key_prefix (str): Custom prefix for cache key
        vary_on_user (bool): Include user ID in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return func(self, request, *args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or f"{self.__class__.__name__}_{func.__name__}"
            cache_key = generate_cache_key(prefix, request, *args, **kwargs)
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return Response(cached_response)
            
            # Execute the original function
            response = func(self, request, *args, **kwargs)
            
            # Cache successful responses
            if isinstance(response, Response) and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
                logger.debug(f"Cached response for key: {cache_key}")
            
            return response
        
        return wrapper
    return decorator


def cache_api_view(timeout=300, key_prefix=None, vary_on_user=True):
    """
    Decorator for caching API views (function-based views).
    
    Args:
        timeout (int): Cache timeout in seconds (default: 5 minutes)
        key_prefix (str): Custom prefix for cache key
        vary_on_user (bool): Include user ID in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return func(request, *args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, request, *args, **kwargs)
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return Response(cached_response)
            
            # Execute the original function
            response = func(request, *args, **kwargs)
            
            # Cache successful responses
            if isinstance(response, Response) and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
                logger.debug(f"Cached response for key: {cache_key}")
            
            return response
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate cache keys matching a pattern.
    
    Args:
        pattern (str): Pattern to match cache keys (e.g., "ScanStatisticsViewSet_*")
    """
    try:
        # Note: This is a simplified implementation
        # In production, consider using Redis with pattern matching
        # or maintaining a list of cache keys for each pattern
        
        # For Django's default cache backend, we need to track keys manually
        # This is a limitation of the default cache backend
        logger.info(f"Cache invalidation requested for pattern: {pattern}")
        
        # You could implement a more sophisticated cache invalidation system here
        # For now, we'll rely on cache timeouts
        
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {str(e)}")


class CacheManager:
    """Utility class for managing cache operations."""
    
    @staticmethod
    def clear_user_cache(user_id):
        """Clear all cached data for a specific user."""
        try:
            # This would require a more sophisticated cache key tracking system
            # For now, we'll log the request
            logger.info(f"Cache clear requested for user: {user_id}")
        except Exception as e:
            logger.error(f"Error clearing cache for user {user_id}: {str(e)}")
    
    @staticmethod
    def warm_cache(viewset_class, action_name, request_data):
        """Pre-populate cache with data (cache warming)."""
        try:
            logger.info(f"Cache warming requested for {viewset_class.__name__}.{action_name}")
            # Implementation would depend on specific requirements
        except Exception as e:
            logger.error(f"Error warming cache: {str(e)}")


# Predefined decorators for common use cases
cache_stats_endpoint = cache_viewset_action(
    timeout=300,  # 5 minutes
    key_prefix="stats",
    vary_on_user=True
)

cache_dashboard_data = cache_api_view(
    timeout=180,  # 3 minutes
    key_prefix="dashboard",
    vary_on_user=True
)

cache_threat_data = cache_viewset_action(
    timeout=600,  # 10 minutes
    key_prefix="threats",
    vary_on_user=False  # Threat data is global
)