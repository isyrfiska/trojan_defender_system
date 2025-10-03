"""
Health check endpoints for monitoring system status.
"""

import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.contrib.auth import get_user_model

from .cache_utils import default_cache, session_cache, rate_limit_cache

logger = logging.getLogger(__name__)

User = get_user_model()


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with system status
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check cache connectivity
    cache_status = {}
    
    # Test default cache
    try:
        test_key = f"health_check_{int(time.time())}"
        default_cache.cache.set(test_key, "test", 10)
        retrieved = default_cache.cache.get(test_key)
        default_cache.cache.delete(test_key)
        
        cache_status['default'] = "healthy" if retrieved == "test" else "unhealthy"
    except Exception as e:
        logger.error(f"Default cache health check failed: {e}")
        cache_status['default'] = "unhealthy"
    
    # Test session cache
    try:
        test_key = f"session_health_check_{int(time.time())}"
        session_cache.cache.set(test_key, "test", 10)
        retrieved = session_cache.cache.get(test_key)
        session_cache.cache.delete(test_key)
        
        cache_status['sessions'] = "healthy" if retrieved == "test" else "unhealthy"
    except Exception as e:
        logger.error(f"Session cache health check failed: {e}")
        cache_status['sessions'] = "unhealthy"
    
    # Test rate limit cache
    try:
        test_key = f"rate_limit_health_check_{int(time.time())}"
        rate_limit_cache.cache.set(test_key, "test", 10)
        retrieved = rate_limit_cache.cache.get(test_key)
        rate_limit_cache.cache.delete(test_key)
        
        cache_status['rate_limit'] = "healthy" if retrieved == "test" else "unhealthy"
    except Exception as e:
        logger.error(f"Rate limit cache health check failed: {e}")
        cache_status['rate_limit'] = "unhealthy"
    
    # Overall status
    overall_status = "healthy"
    if db_status != "healthy" or any(status != "healthy" for status in cache_status.values()):
        overall_status = "degraded"
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "cache": cache_status
        }
    }
    
    status_code = 200 if overall_status == "healthy" else 503
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def detailed_health_check(request):
    """
    Detailed health check with system metrics.
    
    Returns:
        JSON response with detailed system status and metrics
    """
    try:
        # Database metrics
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scanner_scanresult")
            scan_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM threatmap_threatevent")
            threat_count = cursor.fetchone()[0]
        
        db_metrics = {
            "status": "healthy",
            "users": user_count,
            "scans": scan_count,
            "threats": threat_count
        }
    except Exception as e:
        logger.error(f"Database metrics collection failed: {e}")
        db_metrics = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Cache metrics
    cache_metrics = {}
    
    # Default cache stats
    try:
        stats = default_cache.get_stats()
        cache_metrics['default'] = {
            "status": "healthy",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Default cache metrics failed: {e}")
        cache_metrics['default'] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Session cache stats
    try:
        stats = session_cache.get_stats()
        cache_metrics['sessions'] = {
            "status": "healthy",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Session cache metrics failed: {e}")
        cache_metrics['sessions'] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Rate limit cache stats
    try:
        stats = rate_limit_cache.get_stats()
        cache_metrics['rate_limit'] = {
            "status": "healthy",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Rate limit cache metrics failed: {e}")
        cache_metrics['rate_limit'] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # System info
    system_info = {
        "debug": settings.DEBUG,
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "environment": getattr(settings, 'ENVIRONMENT', 'development')
    }
    
    # Overall status
    overall_status = "healthy"
    if (db_metrics.get("status") != "healthy" or 
        any(cache.get("status") != "healthy" for cache in cache_metrics.values())):
        overall_status = "degraded"
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "system": system_info,
        "database": db_metrics,
        "cache": cache_metrics
    }
    
    status_code = 200 if overall_status == "healthy" else 503
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def cache_status(request):
    """
    Cache-specific status endpoint.
    
    Returns:
        JSON response with cache status and statistics
    """
    cache_info = {}
    
    # Get stats for all cache backends
    cache_backends = {
        'default': default_cache,
        'sessions': session_cache,
        'rate_limit': rate_limit_cache
    }
    
    for name, cache_manager in cache_backends.items():
        try:
            stats = cache_manager.get_stats()
            
            # Test cache functionality
            test_key = f"cache_test_{name}_{int(time.time())}"
            cache_manager.cache.set(test_key, "test_value", 10)
            test_result = cache_manager.cache.get(test_key)
            cache_manager.cache.delete(test_key)
            
            cache_info[name] = {
                "status": "healthy" if test_result == "test_value" else "unhealthy",
                "stats": stats,
                "test_passed": test_result == "test_value"
            }
            
        except Exception as e:
            logger.error(f"Cache status check failed for {name}: {e}")
            cache_info[name] = {
                "status": "unhealthy",
                "error": str(e),
                "test_passed": False
            }
    
    # Overall cache status
    overall_status = "healthy"
    if any(info.get("status") != "healthy" for info in cache_info.values()):
        overall_status = "degraded"
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "caches": cache_info
    }
    
    status_code = 200 if overall_status == "healthy" else 503
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["POST"])
def cache_clear(request):
    """
    Clear cache endpoint (for admin use).
    
    Returns:
        JSON response confirming cache clear operation
    """
    # This should be protected in production
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    try:
        # Clear all caches
        default_cache.cache.clear()
        session_cache.cache.clear()
        rate_limit_cache.cache.clear()
        
        logger.info(f"Cache cleared by user {request.user.id}")
        
        return JsonResponse({
            "status": "success",
            "message": "All caches cleared successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return JsonResponse({
            "status": "error",
            "message": f"Cache clear failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        JSON response indicating if the service is ready to serve traffic
    """
    try:
        # Check if we can connect to database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check if we can connect to cache
        test_key = f"readiness_check_{int(time.time())}"
        default_cache.cache.set(test_key, "ready", 5)
        default_cache.cache.delete(test_key)
        
        return JsonResponse({
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        JSON response indicating if the service is alive
    """
    return JsonResponse({
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    })