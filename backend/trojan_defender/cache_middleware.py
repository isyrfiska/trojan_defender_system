"""
Cache middleware for automatic cache management and invalidation.
"""

import logging
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .cache_utils import invalidate_user_cache, default_cache

logger = logging.getLogger(__name__)

User = get_user_model()


class CacheInvalidationMiddleware(MiddlewareMixin):
    """
    Middleware to handle automatic cache invalidation based on user actions.
    """
    
    def process_request(self, request):
        """Process incoming request."""
        # Add cache stats to request for debugging
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.cache_stats = default_cache.get_stats()
        return None
    
    def process_response(self, request, response):
        """Process outgoing response."""
        # Add cache headers for debugging in development
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request, '_cache_hit'):
                response['X-Cache-Status'] = 'HIT'
            else:
                response['X-Cache-Status'] = 'MISS'
        
        return response


# Signal handlers for automatic cache invalidation

@receiver(user_logged_in)
def invalidate_cache_on_login(sender, request, user, **kwargs):
    """Invalidate user cache when user logs in."""
    try:
        invalidate_user_cache(user.id)
        logger.info(f"Invalidated cache for user {user.id} on login")
    except Exception as e:
        logger.error(f"Failed to invalidate cache on login for user {user.id}: {e}")


@receiver(user_logged_out)
def invalidate_cache_on_logout(sender, request, user, **kwargs):
    """Invalidate user cache when user logs out."""
    try:
        if user:
            invalidate_user_cache(user.id)
            logger.info(f"Invalidated cache for user {user.id} on logout")
    except Exception as e:
        logger.error(f"Failed to invalidate cache on logout: {e}")


@receiver(post_save, sender=User)
def invalidate_user_cache_on_save(sender, instance, created, **kwargs):
    """Invalidate user cache when user model is saved."""
    try:
        invalidate_user_cache(instance.id)
        action = "created" if created else "updated"
        logger.info(f"Invalidated cache for user {instance.id} on {action}")
    except Exception as e:
        logger.error(f"Failed to invalidate user cache on save: {e}")


@receiver(post_delete, sender=User)
def invalidate_user_cache_on_delete(sender, instance, **kwargs):
    """Invalidate user cache when user is deleted."""
    try:
        invalidate_user_cache(instance.id)
        logger.info(f"Invalidated cache for user {instance.id} on delete")
    except Exception as e:
        logger.error(f"Failed to invalidate user cache on delete: {e}")


# Cache warming functions

def warm_user_cache(user_id):
    """
    Warm up cache for a specific user.
    
    Args:
        user_id: ID of the user to warm cache for
    """
    try:
        from users.serializers import UserSerializer
        from scanner.models import ScanResult
        from threatmap.models import ThreatEvent
        
        user = User.objects.get(id=user_id)
        
        # Warm user profile cache
        serializer = UserSerializer(user)
        cache_key = f"user_profile:{user_id}"
        default_cache.cache.set(cache_key, serializer.data, 1800)
        
        # Warm user statistics cache
        user_stats = {
            'total_scans': ScanResult.objects.filter(user=user).count(),
            'total_threats': ThreatEvent.objects.filter(user=user).count(),
        }
        stats_cache_key = f"user_stats:{user_id}"
        default_cache.cache.set(stats_cache_key, user_stats, 900)
        
        logger.info(f"Warmed cache for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to warm cache for user {user_id}: {e}")


def warm_global_cache():
    """
    Warm up global cache entries.
    """
    try:
        from scanner.models import ScanResult, ScanThreat
        from threatmap.models import ThreatEvent
        
        # Warm global statistics
        global_stats = {
            'total_scans': ScanResult.objects.count(),
            'total_threats': ScanThreat.objects.count(),
            'total_events': ThreatEvent.objects.count(),
            'total_users': User.objects.count(),
        }
        
        cache_key = "global_stats"
        default_cache.cache.set(cache_key, global_stats, 600)  # 10 minutes
        
        logger.info("Warmed global cache")
        
    except Exception as e:
        logger.error(f"Failed to warm global cache: {e}")


class CacheWarmupMiddleware(MiddlewareMixin):
    """
    Middleware to warm up cache for authenticated users.
    """
    
    def process_request(self, request):
        """Warm up cache for authenticated users."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if user cache exists, if not, warm it up
            cache_key = f"user_profile:{request.user.id}"
            if not default_cache.cache.get(cache_key):
                # Warm up cache in background (don't block request)
                try:
                    from django.core.management import call_command
                    # This would ideally be done with Celery in production
                    warm_user_cache(request.user.id)
                except Exception as e:
                    logger.debug(f"Cache warmup failed for user {request.user.id}: {e}")
        
        return None


class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to add cache control headers to responses.
    """
    
    # Define cache settings for different URL patterns
    CACHE_SETTINGS = {
        '/api/scanner/statistics/': {'max_age': 300, 'public': False},
        '/api/threatmap/map_data/': {'max_age': 600, 'public': False},
        '/api/users/profile/': {'max_age': 1800, 'public': False},
        '/api/static/': {'max_age': 86400, 'public': True},  # 24 hours for static files
    }
    
    def process_response(self, request, response):
        """Add appropriate cache control headers."""
        path = request.path
        
        # Find matching cache setting
        cache_setting = None
        for pattern, setting in self.CACHE_SETTINGS.items():
            if path.startswith(pattern):
                cache_setting = setting
                break
        
        if cache_setting:
            max_age = cache_setting['max_age']
            is_public = cache_setting['public']
            
            if is_public:
                response['Cache-Control'] = f'public, max-age={max_age}'
            else:
                response['Cache-Control'] = f'private, max-age={max_age}'
            
            # Add ETag for better caching without forcing premature rendering
            try:
                if not getattr(response, 'streaming', False):
                    # Ensure response is rendered if necessary (DRF Response/TemplateResponse)
                    if hasattr(response, 'render') and not getattr(response, 'is_rendered', True):
                        response = response.render()
                    content = getattr(response, 'content', b'')
                    if content:
                        import hashlib
                        etag = hashlib.md5(content).hexdigest()
                        response['ETag'] = f'"{etag}"'
            except Exception as e:
                # Never break the response pipeline due to ETag issues
                logger.debug(f'ETag generation skipped: {e}')
        
        return response