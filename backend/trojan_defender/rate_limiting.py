import time
import logging
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import Throttled

logger = logging.getLogger('api')
security_logger = logging.getLogger('django.security')

class RateLimitExceeded(Throttled):
    """Custom exception for rate limit exceeded."""
    default_detail = 'Request rate limit exceeded.'
    default_code = 'throttled'


class RateLimiter:
    """
    Rate limiter utility class that provides methods for rate limiting.
    
    This class implements various rate limiting strategies:
    - Fixed window rate limiting
    - Sliding window rate limiting
    - Token bucket algorithm
    """
    
    @staticmethod
    def get_client_identifier(request):
        """
        Get a unique identifier for the client making the request.
        
        Uses authenticated user ID if available, otherwise falls back to IP address.
        """
        # Safety check: ensure request has required attributes
        if not hasattr(request, 'META'):
            # Fallback to a default identifier if request is malformed
            return "unknown:request"
        
        # Safely check if user attribute exists and is authenticated
        # Use getattr to avoid AttributeError if user doesn't exist yet
        user = getattr(request, 'user', None)
        if (user is not None and 
            hasattr(user, 'is_authenticated') and 
            callable(getattr(user, 'is_authenticated', None)) and 
            user.is_authenticated):
            return f"user:{user.id}"
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip:{ip}"
    
    @staticmethod
    def fixed_window_rate_limit(request, key_prefix, limit, period):
        """
        Implement fixed window rate limiting.
        
        Args:
            request: The HTTP request object
            key_prefix: Prefix for the cache key
            limit: Maximum number of requests allowed in the period
            period: Time period in seconds
            
        Returns:
            tuple: (allowed, current_count, wait_seconds)
        """
        client_id = RateLimiter.get_client_identifier(request)
        window = int(time.time() / period)
        cache_key = f"{key_prefix}:{client_id}:{window}"
        
        # Get current count
        count = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if count >= limit:
            # Calculate time until next window
            next_window = (window + 1) * period
            wait_seconds = next_window - time.time()
            return False, count, int(wait_seconds) + 1
        
        # Increment counter
        cache.set(cache_key, count + 1, period)
        return True, count + 1, 0
    
    @staticmethod
    def sliding_window_rate_limit(request, key_prefix, limit, period):
        """
        Implement sliding window rate limiting.
        
        Args:
            request: The HTTP request object
            key_prefix: Prefix for the cache key
            limit: Maximum number of requests allowed in the period
            period: Time period in seconds
            
        Returns:
            tuple: (allowed, current_count, wait_seconds)
        """
        client_id = RateLimiter.get_client_identifier(request)
        now = time.time()
        cache_key = f"{key_prefix}:{client_id}:sliding"
        
        # Get timestamps of previous requests
        timestamps = cache.get(cache_key, [])
        
        # Remove timestamps outside the window
        valid_timestamps = [ts for ts in timestamps if ts > now - period]
        
        # Check if limit exceeded
        if len(valid_timestamps) >= limit:
            # Calculate wait time (time until oldest request expires)
            wait_seconds = valid_timestamps[0] - (now - period)
            return False, len(valid_timestamps), int(wait_seconds) + 1
        
        # Add current timestamp
        valid_timestamps.append(now)
        cache.set(cache_key, valid_timestamps, period * 2)  # Store for twice the period to handle sliding window
        
        return True, len(valid_timestamps), 0
    
    @staticmethod
    def token_bucket_rate_limit(request, key_prefix, rate, capacity):
        """
        Implement token bucket rate limiting algorithm.
        
        Args:
            request: The HTTP request object
            key_prefix: Prefix for the cache key
            rate: Token refill rate per second
            capacity: Maximum bucket capacity
            
        Returns:
            tuple: (allowed, tokens_left, wait_seconds)
        """
        client_id = RateLimiter.get_client_identifier(request)
        now = time.time()
        
        # Cache keys for last update time and tokens
        last_update_key = f"{key_prefix}:{client_id}:last_update"
        tokens_key = f"{key_prefix}:{client_id}:tokens"
        
        # Get last update time and tokens
        last_update = cache.get(last_update_key, now)
        tokens = cache.get(tokens_key, capacity)
        
        # Calculate token refill
        time_passed = now - last_update
        new_tokens = tokens + (time_passed * rate)
        
        # Cap tokens at capacity
        if new_tokens > capacity:
            new_tokens = capacity
        
        # Check if we have enough tokens
        if new_tokens < 1:
            # Calculate wait time until we have at least one token
            wait_seconds = (1 - new_tokens) / rate
            return False, new_tokens, int(wait_seconds) + 1
        
        # Consume a token
        new_tokens -= 1
        
        # Update cache
        cache.set(last_update_key, now, 86400)  # 24 hours
        cache.set(tokens_key, new_tokens, 86400)  # 24 hours
        
        return True, new_tokens, 0


class RateLimitMiddleware:
    """
    Middleware for implementing rate limiting across the application.
    
    This middleware applies different rate limits based on the request path,
    HTTP method, and user authentication status.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define rate limit rules
        self.rate_limit_rules = [
            # Authentication endpoints - stricter limits
            {
                'path_startswith': '/api/auth/',
                'methods': ['POST'],
                'limit': 5,
                'period': 60,  # 5 requests per minute
                'key_prefix': 'auth',
                'strategy': 'fixed_window',
            },
            # File upload endpoints - limit file uploads
            {
                'path_startswith': '/api/scanner/upload/',
                'methods': ['POST'],
                'limit': 10,
                'period': 3600,  # 10 uploads per hour
                'key_prefix': 'upload',
                'strategy': 'fixed_window',
            },
            # API endpoints - general rate limit
            {
                'path_startswith': '/api/',
                'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
                'limit': 60,
                'period': 60,  # 60 requests per minute
                'key_prefix': 'api',
                'strategy': 'sliding_window',
            },
            # Admin endpoints - protect against brute force
            {
                'path_startswith': '/admin/',
                'methods': ['POST'],
                'limit': 10,
                'period': 300,  # 10 requests per 5 minutes
                'key_prefix': 'admin',
                'strategy': 'token_bucket',
                'rate': 0.05,  # 1 token per 20 seconds
                'capacity': 10,
            },
        ]
    
    def __call__(self, request):
        # Skip rate limiting if disabled
        if not getattr(settings, 'RATELIMIT_ENABLE', True):
            return self.get_response(request)
        
        # Safety check: ensure request has required attributes
        if not hasattr(request, 'method') or not hasattr(request, 'path'):
            return self.get_response(request)
        
        # Check if request matches any rate limit rule
        for rule in self.rate_limit_rules:
            if (request.path.startswith(rule['path_startswith']) and 
                request.method in rule['methods']):
                
                # Apply rate limiting based on strategy
                strategy = rule.get('strategy', 'fixed_window')
                
                if strategy == 'fixed_window':
                    allowed, count, wait = RateLimiter.fixed_window_rate_limit(
                        request, 
                        rule['key_prefix'], 
                        rule['limit'], 
                        rule['period']
                    )
                elif strategy == 'sliding_window':
                    allowed, count, wait = RateLimiter.sliding_window_rate_limit(
                        request, 
                        rule['key_prefix'], 
                        rule['limit'], 
                        rule['period']
                    )
                elif strategy == 'token_bucket':
                    allowed, count, wait = RateLimiter.token_bucket_rate_limit(
                        request, 
                        rule['key_prefix'], 
                        rule.get('rate', 1), 
                        rule.get('capacity', rule['limit'])
                    )
                else:
                    # Default to fixed window
                    allowed, count, wait = RateLimiter.fixed_window_rate_limit(
                        request, 
                        rule['key_prefix'], 
                        rule['limit'], 
                        rule['period']
                    )
                
                # If rate limit exceeded
                if not allowed:
                    client_id = RateLimiter.get_client_identifier(request)
                    
                    # Log rate limit exceeded
                    security_logger.warning(
                        f"Rate limit exceeded: {request.path} ({request.method}) - "
                        f"Client: {client_id}, Rule: {rule['key_prefix']}, "
                        f"Count: {count}, Wait: {wait}s"
                    )
                    
                    # Return rate limit response
                    if request.path.startswith('/api/'):
                        # API response - return fully rendered Django JsonResponse to avoid rendering issues
                        return JsonResponse(
                            {
                                'detail': f'Request rate limit exceeded. Try again in {wait} seconds.',
                                'wait': wait
                            },
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )
                    else:
                        # Regular HTTP response
                        response = HttpResponse(
                            'Too many requests. Please try again later.',
                            status=429
                        )
                        response['Retry-After'] = str(wait)
                        return response
                
                # Log high request rates (80% of limit)
                if count >= rule['limit'] * 0.8:
                    client_id = RateLimiter.get_client_identifier(request)
                    logger.warning(
                        f"High request rate: {request.path} ({request.method}) - "
                        f"Client: {client_id}, Rule: {rule['key_prefix']}, "
                        f"Count: {count}/{rule['limit']}"
                    )
                
                break
        
        # Continue processing the request
        return self.get_response(request)

# Test compatibility shim: Some tests patch RateLimitingMiddleware.get_client_identifier
# Provide an alias class that delegates to RateLimitMiddleware and RateLimiter.
class RateLimitingMiddleware(RateLimitMiddleware):
    @staticmethod
    def get_client_identifier(request):
        return RateLimiter.get_client_identifier(request)