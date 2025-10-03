import logging
import time
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model

# Security logger
security_logger = logging.getLogger('django.security')

User = get_user_model()


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add additional security headers."""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
        
        # Add HSTS header in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        
        return response


class SecurityLoggingMiddleware(MiddlewareMixin):
    """Middleware to log security-related events."""
    
    def process_request(self, request):
        # Log suspicious requests
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        # Log requests with suspicious user agents
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'openvas', 'burp', 'w3af', 'acunetix', 'appscan'
        ]
        
        if any(agent.lower() in user_agent.lower() for agent in suspicious_agents):
            security_logger.warning(
                f'Suspicious user agent detected: {user_agent} from IP: {ip_address}'
            )
        
        # Log requests to sensitive endpoints
        sensitive_paths = ['/admin/', '/api/auth/', '/swagger/', '/redoc/']
        if any(request.path.startswith(path) for path in sensitive_paths):
            security_logger.info(
                f'Access to sensitive endpoint: {request.path} from IP: {ip_address}'
            )
    
    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """Enhanced middleware to protect against brute force attacks."""
    
    def process_request(self, request):
        if request.path in ['/api/auth/token/', '/api/auth/login/', '/admin/login/']:
            ip_address = self.get_client_ip(request)
            username = self.get_username_from_request(request)
            
            # Check both IP and username-based blocking
            ip_blocked_key = f'blocked_ip_{ip_address}'
            user_blocked_key = f'blocked_user_{username}' if username else None
            
            # Check if IP is temporarily blocked
            if cache.get(ip_blocked_key):
                security_logger.warning(
                    f'Blocked IP attempting login: {ip_address}'
                )
                return HttpResponseForbidden('Too many failed login attempts. Please try again later.')
            
            # Check if username is temporarily blocked
            if user_blocked_key and cache.get(user_blocked_key):
                security_logger.warning(
                    f'Blocked username attempting login: {username} from IP: {ip_address}'
                )
                return HttpResponseForbidden('Too many failed login attempts for this account. Please try again later.')
    
    def process_response(self, request, response):
        if request.path in ['/api/auth/token/', '/api/auth/login/', '/admin/login/']:
            ip_address = self.get_client_ip(request)
            username = self.get_username_from_request(request)
            
            ip_cache_key = f'failed_login_attempts_{ip_address}'
            user_cache_key = f'failed_login_attempts_user_{username}' if username else None
            ip_blocked_key = f'blocked_ip_{ip_address}'
            user_blocked_key = f'blocked_user_{username}' if username else None
            
            if response.status_code == 401:  # Failed login
                # Track IP-based attempts with progressive delays
                ip_attempts = cache.get(ip_cache_key, 0) + 1
                
                # Calculate progressive timeout (exponential backoff)
                if ip_attempts <= 3:
                    timeout = 300  # 5 minutes for first 3 attempts
                elif ip_attempts <= 5:
                    timeout = 900  # 15 minutes for attempts 4-5
                elif ip_attempts <= 10:
                    timeout = 3600  # 1 hour for attempts 6-10
                else:
                    timeout = 7200  # 2 hours for more than 10 attempts
                
                cache.set(ip_cache_key, ip_attempts, timeout)
                
                # Block IP after 5 failed attempts
                if ip_attempts >= 5:
                    cache.set(ip_blocked_key, True, timeout)
                    security_logger.warning(
                        f'IP blocked due to repeated failed login attempts: {ip_address} (attempt #{ip_attempts})'
                    )
                
                # Track username-based attempts if available
                if username and user_cache_key and user_blocked_key:
                    user_attempts = cache.get(user_cache_key, 0) + 1
                    cache.set(user_cache_key, user_attempts, 1800)  # 30 minutes
                    
                    # Block username after 3 failed attempts
                    if user_attempts >= 3:
                        cache.set(user_blocked_key, True, 1800)  # Block for 30 minutes
                        security_logger.warning(
                            f'Username blocked due to repeated failed login attempts: {username} from IP: {ip_address}'
                        )
                
                security_logger.warning(
                    f'Failed login attempt #{ip_attempts} from IP: {ip_address}, username: {username or "unknown"}'
                )
                
            elif response.status_code == 200:  # Successful login
                # Clear failed attempts on successful login
                cache.delete(ip_cache_key)
                cache.delete(ip_blocked_key)
                if user_cache_key and user_blocked_key:
                    cache.delete(user_cache_key)
                    cache.delete(user_blocked_key)
                
                security_logger.info(
                    f'Successful login from IP: {ip_address}, username: {username or "unknown"}'
                )
        
        return response
    
    def get_username_from_request(self, request):
        """Extract username from request data."""
        try:
            if hasattr(request, 'data') and request.data:
                return request.data.get('username') or request.data.get('email')
            elif request.POST:
                return request.POST.get('username') or request.POST.get('email')
        except:
            pass
        return None
    
    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestSizeMiddleware(MiddlewareMixin):
    """Middleware to limit request size for security."""
    
    def process_request(self, request):
        # Limit request size (default 10MB)
        max_size = getattr(settings, 'MAX_REQUEST_SIZE', 10485760)
        
        if hasattr(request, 'META') and 'CONTENT_LENGTH' in request.META:
            content_length_str = request.META['CONTENT_LENGTH']
            if content_length_str and content_length_str.isdigit():
                content_length = int(content_length_str)
                if content_length > max_size:
                    security_logger.warning(
                        f'Request size too large: {content_length} bytes from IP: {self.get_client_ip(request)}'
                    )
                    return HttpResponseForbidden('Request entity too large')
    
    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """Middleware to enhance session security."""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Check for session hijacking
            session_ip = request.session.get('ip_address')
            current_ip = self.get_client_ip(request)
            
            if session_ip and session_ip != current_ip:
                security_logger.warning(
                    f'Potential session hijacking detected. Session IP: {session_ip}, Current IP: {current_ip}, User: {request.user.email}'
                )
                # Optionally, you can logout the user here
                # logout(request)
                # return HttpResponseForbidden('Session security violation detected')
            
            # Store IP address in session
            if not session_ip:
                request.session['ip_address'] = current_ip
            
            # Update last activity
            request.session['last_activity'] = time.time()
    
    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip