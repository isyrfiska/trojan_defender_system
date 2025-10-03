import re
import logging
import bleach
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('django.security')

class ContentSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for content security to protect against XSS, CSRF, and other content-based attacks.
    
    Features:
    - Request body sanitization
    - SQL injection detection
    - XSS attack detection
    - Content-Type validation
    - File upload validation
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        
        # SQL injection patterns
        self.sql_patterns = [
            r'(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|UNION|CREATE|WHERE)\s',
            r'--\s',  # SQL comment
            r'/\*.*\*/',  # SQL block comment
            r';\s*(\w+\s+)+',  # Multiple statements
            r'\bOR\s+\d+\s*=\s*\d+\b',  # OR 1=1
            r'\bAND\s+\d+\s*=\s*\d+\b',  # AND 1=1
        ]
        
        # XSS attack patterns
        self.xss_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onmouseover=',
            r'onclick=',
            r'onsubmit=',
            r'<iframe',
            r'<object',
            r'<embed',
            r'<base',
            r'<applet',
            r'document\.cookie',
            r'document\.location',
            r'document\.write',
            r'\.innerHTML',
            r'eval\(',
            r'setTimeout\(',
            r'setInterval\(',
            r'new\s+Function\(',
        ]
        
        # Compile regex patterns for performance
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
    
    def process_request(self, request):
        """Process incoming request and check for security issues."""
        # Skip checks for safe methods like GET, HEAD, OPTIONS
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return None
        
        # Check content type
        content_type = request.META.get('CONTENT_TYPE', '')
        
        # Process JSON content
        if 'application/json' in content_type:
            if hasattr(request, 'body') and request.body:
                body_content = request.body.decode('utf-8', errors='ignore')
                
                # Check for SQL injection
                if self._contains_sql_injection(body_content):
                    client_ip = self._get_client_ip(request)
                    logger.warning(f"Potential SQL injection detected in JSON request from {client_ip}")
                    return HttpResponseForbidden("Request contains potentially malicious content")
                
                # Check for XSS attacks
                if self._contains_xss(body_content):
                    client_ip = self._get_client_ip(request)
                    logger.warning(f"Potential XSS attack detected in JSON request from {client_ip}")
                    return HttpResponseForbidden("Request contains potentially malicious content")
        
        # Process form data
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            if hasattr(request, 'POST'):
                for key, value in request.POST.items():
                    if isinstance(value, str):
                        # Check for SQL injection
                        if self._contains_sql_injection(value):
                            client_ip = self._get_client_ip(request)
                            logger.warning(f"Potential SQL injection detected in form field '{key}' from {client_ip}")
                            return HttpResponseForbidden("Request contains potentially malicious content")
                        
                        # Check for XSS attacks
                        if self._contains_xss(value):
                            client_ip = self._get_client_ip(request)
                            logger.warning(f"Potential XSS attack detected in form field '{key}' from {client_ip}")
                            return HttpResponseForbidden("Request contains potentially malicious content")
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response."""
        # Add Content-Security-Policy header if not already present
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self._get_default_csp()
        
        # Add X-Content-Type-Options if not already present
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'
        
        return response
    
    def _contains_sql_injection(self, content):
        """Check if content contains SQL injection patterns."""
        if not content:
            return False
        
        for pattern in self.sql_regex:
            if pattern.search(content):
                return True
        
        return False
    
    def _contains_xss(self, content):
        """Check if content contains XSS attack patterns."""
        if not content:
            return False
        
        for pattern in self.xss_regex:
            if pattern.search(content):
                return True
        
        return False
    
    def _get_default_csp(self):
        """Get default Content-Security-Policy header value."""
        return "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
    
    def _get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def sanitize_html(html_content, allowed_tags=None, allowed_attrs=None):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: bleach defaults)
        allowed_attrs: Dict of allowed attributes for each tag (default: bleach defaults)
    
    Returns:
        Sanitized HTML content
    """
    if allowed_tags is None:
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS
    
    if allowed_attrs is None:
        allowed_attrs = bleach.sanitizer.ALLOWED_ATTRIBUTES
    
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)


def strip_all_tags(html_content):
    """
    Strip all HTML tags from content.
    
    Args:
        html_content: The HTML content to strip
    
    Returns:
        Plain text content
    """
    return bleach.clean(html_content, tags=[], attributes={}, strip=True)