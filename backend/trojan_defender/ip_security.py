import logging
import ipaddress
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.security')

class IPSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for IP-based security controls.
    
    Features:
    - IP blocklist/allowlist
    - Country-based blocking
    - Tor exit node blocking
    - VPN detection
    - Automatic blocking of suspicious IPs
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.blocklist = getattr(settings, 'IP_BLOCKLIST', [])
        self.allowlist = getattr(settings, 'IP_ALLOWLIST', [])
        self.blocked_countries = getattr(settings, 'BLOCKED_COUNTRIES', [])
        self.block_tor_exit_nodes = getattr(settings, 'BLOCK_TOR_EXIT_NODES', True)
        self.block_vpns = getattr(settings, 'BLOCK_VPNS', False)
        
        # Convert string IPs/CIDRs to network objects for efficient checking
        self._blocklist_networks = []
        self._allowlist_networks = []
        
        for ip in self.blocklist:
            try:
                if '/' in ip:
                    self._blocklist_networks.append(ipaddress.ip_network(ip, strict=False))
                else:
                    self._blocklist_networks.append(ipaddress.ip_address(ip))
            except ValueError:
                logger.error(f"Invalid IP or CIDR in blocklist: {ip}")
        
        for ip in self.allowlist:
            try:
                if '/' in ip:
                    self._allowlist_networks.append(ipaddress.ip_network(ip, strict=False))
                else:
                    self._allowlist_networks.append(ipaddress.ip_address(ip))
            except ValueError:
                logger.error(f"Invalid IP or CIDR in allowlist: {ip}")
    
    def process_request(self, request):
        """Process incoming request and apply IP security rules."""
        client_ip = self.get_client_ip(request)
        
        # Skip checks for local development
        if settings.DEBUG and client_ip in ('127.0.0.1', '::1'):
            return None
        
        # Check if IP is in allowlist (allowlist overrides blocklist)
        if self._is_ip_in_allowlist(client_ip):
            return None
        
        # Check if IP is in blocklist
        if self._is_ip_in_blocklist(client_ip):
            logger.warning(f"Blocked request from blocklisted IP: {client_ip}")
            return HttpResponseForbidden("Access denied")
        
        # Check if IP is from a blocked country
        if self.blocked_countries and self._is_ip_from_blocked_country(client_ip):
            logger.warning(f"Blocked request from IP in blocked country: {client_ip}")
            return HttpResponseForbidden("Access denied from your region")
        
        # Check if IP is a Tor exit node
        if self.block_tor_exit_nodes and self._is_tor_exit_node(client_ip):
            logger.warning(f"Blocked request from Tor exit node: {client_ip}")
            return HttpResponseForbidden("Access via Tor network is not allowed")
        
        # Check if IP is a VPN
        if self.block_vpns and self._is_vpn_ip(client_ip):
            logger.warning(f"Blocked request from VPN IP: {client_ip}")
            return HttpResponseForbidden("Access via VPN is not allowed")
        
        # Check if IP is automatically blocked due to suspicious activity
        if self._is_ip_auto_blocked(client_ip):
            logger.warning(f"Blocked request from auto-blocked IP: {client_ip}")
            return HttpResponseForbidden("Access temporarily restricted due to suspicious activity")
        
        return None
    
    def _is_ip_in_blocklist(self, ip_str):
        """Check if an IP is in the blocklist."""
        try:
            ip = ipaddress.ip_address(ip_str)
            
            # Check direct IP match
            if ip in self._blocklist_networks:
                return True
            
            # Check if IP is in any blocked network
            for network in self._blocklist_networks:
                if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
                    if ip in network:
                        return True
            
            return False
        except ValueError:
            logger.error(f"Invalid IP address: {ip_str}")
            return False
    
    def _is_ip_in_allowlist(self, ip_str):
        """Check if an IP is in the allowlist."""
        if not self._allowlist_networks:
            return False
            
        try:
            ip = ipaddress.ip_address(ip_str)
            
            # Check direct IP match
            if ip in self._allowlist_networks:
                return True
            
            # Check if IP is in any allowed network
            for network in self._allowlist_networks:
                if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
                    if ip in network:
                        return True
            
            return False
        except ValueError:
            logger.error(f"Invalid IP address: {ip_str}")
            return False
    
    def _is_ip_from_blocked_country(self, ip_str):
        """Check if an IP is from a blocked country."""
        if not self.blocked_countries:
            return False
        
        # Use cache to avoid repeated lookups
        cache_key = f"ip_country:{ip_str}"
        country_code = cache.get(cache_key)
        
        if country_code is None:
            # In a real implementation, this would use a GeoIP database
            # For this example, we'll just return False
            # In production, you would use:
            # - Django GeoIP2 (django.contrib.gis.geoip2)
            # - A third-party geolocation API
            country_code = self._get_country_code(ip_str)
            cache.set(cache_key, country_code, 86400)  # Cache for 24 hours
        
        return country_code in self.blocked_countries
    
    def _get_country_code(self, ip_str):
        """Get country code for an IP address."""
        # This is a placeholder. In a real implementation, you would use:
        # - Django GeoIP2: from django.contrib.gis.geoip2 import GeoIP2
        # - Or a third-party geolocation API
        return ""
    
    def _is_tor_exit_node(self, ip_str):
        """Check if an IP is a Tor exit node."""
        # Use cache to avoid repeated lookups
        cache_key = f"tor_exit_node:{ip_str}"
        is_tor = cache.get(cache_key)
        
        if is_tor is None:
            # In a real implementation, this would check against a list of Tor exit nodes
            # For this example, we'll just return False
            is_tor = False
            cache.set(cache_key, is_tor, 3600)  # Cache for 1 hour
        
        return is_tor
    
    def _is_vpn_ip(self, ip_str):
        """Check if an IP is from a VPN provider."""
        # Use cache to avoid repeated lookups
        cache_key = f"vpn_ip:{ip_str}"
        is_vpn = cache.get(cache_key)
        
        if is_vpn is None:
            # In a real implementation, this would check against a list of known VPN IPs
            # For this example, we'll just return False
            is_vpn = False
            cache.set(cache_key, is_vpn, 3600)  # Cache for 1 hour
        
        return is_vpn
    
    def _is_ip_auto_blocked(self, ip_str):
        """Check if an IP is automatically blocked due to suspicious activity."""
        cache_key = f"auto_blocked_ip:{ip_str}"
        return cache.get(cache_key, False)
    
    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def auto_block_ip(ip, duration=3600, reason="suspicious_activity"):
    """
    Automatically block an IP address for a specified duration.
    
    Args:
        ip: The IP address to block
        duration: Duration in seconds (default: 1 hour)
        reason: Reason for blocking
    """
    cache_key = f"auto_blocked_ip:{ip}"
    cache.set(cache_key, True, duration)
    
    # Log the auto-block
    logger.warning(f"Auto-blocked IP {ip} for {duration} seconds. Reason: {reason}")


def is_ip_auto_blocked(ip):
    """Check if an IP is automatically blocked."""
    cache_key = f"auto_blocked_ip:{ip}"
    return cache.get(cache_key, False)


def unblock_ip(ip):
    """Remove an IP from the auto-block list."""
    cache_key = f"auto_blocked_ip:{ip}"
    cache.delete(cache_key)
    logger.info(f"Unblocked IP: {ip}")