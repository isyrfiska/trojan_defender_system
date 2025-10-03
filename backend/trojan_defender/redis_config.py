"""
Optimized Redis Configuration for Trojan Defender
Provides enhanced Redis connection management, pooling, and performance optimizations.
"""

import os
import time
import redis
import logging
import random
from redis.connection import ConnectionPool, SSLConnection, Connection
from redis.sentinel import Sentinel
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


class ExponentialBackoffRetry:
    """Implements exponential backoff retry logic for Redis connections."""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError, ConnectionRefusedError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Redis operation failed after {self.max_retries} attempts: {e}")
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                jitter = random.uniform(0, delay * 0.1)  # Add 10% jitter
                total_delay = delay + jitter
                
                logger.warning(f"Redis operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. Retrying in {total_delay:.2f}s")
                time.sleep(total_delay)
        
        raise last_exception


class OptimizedRedisConfig:
    """Optimized Redis configuration with connection pooling and failover support."""
    
    def __init__(self):
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        self.redis_password = os.environ.get('REDIS_PASSWORD', None)
        self.redis_ssl = os.environ.get('REDIS_SSL', 'False').lower() == 'true'
        
        # SSL/TLS Configuration
        self.ssl_cert_reqs = os.environ.get('REDIS_SSL_CERT_REQS', 'required')
        self.ssl_ca_certs = os.environ.get('REDIS_SSL_CA_CERTS', None)
        self.ssl_certfile = os.environ.get('REDIS_SSL_CERTFILE', None)
        self.ssl_keyfile = os.environ.get('REDIS_SSL_KEYFILE', None)
        
        # Connection pool settings
        self.max_connections = int(os.environ.get('REDIS_MAX_CONNECTIONS', '100'))
        self.connection_timeout = int(os.environ.get('REDIS_CONNECTION_TIMEOUT', '5'))
        self.socket_timeout = int(os.environ.get('REDIS_SOCKET_TIMEOUT', '5'))
        self.socket_keepalive = True
        self.socket_keepalive_options = {}
        
        # Health check settings
        self.health_check_interval = int(os.environ.get('REDIS_HEALTH_CHECK_INTERVAL', '30'))
        
        # Retry settings
        self.max_retries = int(os.environ.get('REDIS_MAX_RETRIES', '5'))
        self.retry_base_delay = float(os.environ.get('REDIS_RETRY_BASE_DELAY', '1.0'))
        self.retry_max_delay = float(os.environ.get('REDIS_RETRY_MAX_DELAY', '60.0'))
        
        # Sentinel settings (for high availability)
        self.use_sentinel = os.environ.get('REDIS_USE_SENTINEL', 'False').lower() == 'true'
        self.sentinel_hosts = self._parse_sentinel_hosts()
        self.sentinel_service_name = os.environ.get('REDIS_SENTINEL_SERVICE_NAME', 'mymaster')
        
        self._connection_pools = {}
        self._sentinel = None
        self._retry_handler = ExponentialBackoffRetry(
            max_retries=self.max_retries,
            base_delay=self.retry_base_delay,
            max_delay=self.retry_max_delay
        )
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate Redis configuration parameters."""
        if self.redis_port < 1 or self.redis_port > 65535:
            raise ValueError(f"Invalid Redis port: {self.redis_port}")
        
        if self.max_connections < 1:
            raise ValueError(f"Invalid max_connections: {self.max_connections}")
        
        if self.connection_timeout < 1:
            raise ValueError(f"Invalid connection_timeout: {self.connection_timeout}")
        
        if self.redis_ssl and not self._is_ssl_properly_configured():
            logger.warning("SSL is enabled but SSL certificates are not properly configured")
    
    def _is_ssl_properly_configured(self) -> bool:
        """Check if SSL is properly configured."""
        if not self.redis_ssl:
            return True
        
        # For development, we might not have certificates
        if os.environ.get('DJANGO_ENV', 'development') == 'development':
            return True
        
        return bool(self.ssl_ca_certs or self.ssl_certfile)
        
    def _parse_sentinel_hosts(self) -> list:
        """Parse sentinel hosts from environment variable."""
        sentinel_hosts_str = os.environ.get('REDIS_SENTINEL_HOSTS', '')
        if not sentinel_hosts_str:
            return []
        
        hosts = []
        for host_port in sentinel_hosts_str.split(','):
            host_port = host_port.strip()
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                hosts.append((host, int(port)))
            else:
                hosts.append((host_port, 26379))  # Default sentinel port
        return hosts
    
    def _get_connection_class(self) -> Union[Connection, SSLConnection]:
        """Get appropriate connection class based on SSL configuration."""
        if self.redis_ssl:
            return SSLConnection
        return Connection
    
    def _get_ssl_kwargs(self) -> Dict[str, Any]:
        """Get SSL-specific connection parameters."""
        if not self.redis_ssl:
            return {}
        
        ssl_kwargs = {}
        
        if self.ssl_cert_reqs:
            import ssl
            cert_reqs_map = {
                'none': ssl.CERT_NONE,
                'optional': ssl.CERT_OPTIONAL,
                'required': ssl.CERT_REQUIRED
            }
            ssl_kwargs['ssl_cert_reqs'] = cert_reqs_map.get(self.ssl_cert_reqs.lower(), ssl.CERT_REQUIRED)
        
        if self.ssl_ca_certs:
            ssl_kwargs['ssl_ca_certs'] = self.ssl_ca_certs
        
        if self.ssl_certfile:
            ssl_kwargs['ssl_certfile'] = self.ssl_certfile
        
        if self.ssl_keyfile:
            ssl_kwargs['ssl_keyfile'] = self.ssl_keyfile
        
        return ssl_kwargs
    
    def get_connection_pool(self, db: int = 0) -> ConnectionPool:
        """Get or create an optimized connection pool for the specified database."""
        pool_key = f"db_{db}"
        
        if pool_key not in self._connection_pools:
            connection_class = self._get_connection_class()
            ssl_kwargs = self._get_ssl_kwargs()
            
            base_kwargs = {
                'host': self.redis_host,
                'port': self.redis_port,
                'db': db,
                'password': self.redis_password,
                'max_connections': self.max_connections,
                'socket_timeout': self.socket_timeout,
                'socket_connect_timeout': self.connection_timeout,
                'socket_keepalive': self.socket_keepalive,
                'socket_keepalive_options': self.socket_keepalive_options,
                'health_check_interval': self.health_check_interval,
                'retry_on_timeout': True,
                'retry_on_error': [redis.ConnectionError, redis.TimeoutError],
                'connection_class': connection_class
            }
            
            # Add SSL parameters if SSL is enabled
            base_kwargs.update(ssl_kwargs)
            
            if self.use_sentinel and self.sentinel_hosts:
                # Use Redis Sentinel for high availability
                if not self._sentinel:
                    sentinel_kwargs = {
                        'socket_timeout': self.socket_timeout,
                        'socket_connect_timeout': self.connection_timeout,
                        'socket_keepalive': self.socket_keepalive,
                        'socket_keepalive_options': self.socket_keepalive_options
                    }
                    sentinel_kwargs.update(ssl_kwargs)
                    
                    self._sentinel = Sentinel(self.sentinel_hosts, **sentinel_kwargs)
                
                # Get master connection pool from sentinel
                master_kwargs = {
                    'socket_timeout': self.socket_timeout,
                    'socket_connect_timeout': self.connection_timeout,
                    'socket_keepalive': self.socket_keepalive,
                    'socket_keepalive_options': self.socket_keepalive_options,
                    'db': db,
                    'password': self.redis_password,
                    'health_check_interval': self.health_check_interval,
                    'connection_class': connection_class
                }
                master_kwargs.update(ssl_kwargs)
                
                master = self._sentinel.master_for(self.sentinel_service_name, **master_kwargs)
                self._connection_pools[pool_key] = master.connection_pool
            else:
                # Standard Redis connection pool
                self._connection_pools[pool_key] = ConnectionPool(**base_kwargs)
        
        return self._connection_pools[pool_key]
    
    def get_redis_client(self, db: int = 0) -> redis.Redis:
        """Get an optimized Redis client for the specified database."""
        pool = self.get_connection_pool(db)
        return redis.Redis(connection_pool=pool)
    
    def test_connection(self, db: int = 0) -> bool:
        """Test Redis connection health with retry logic."""
        def _test():
            client = self.get_redis_client(db)
            client.ping()
            return True
        
        try:
            return self._retry_handler.retry_with_backoff(_test)
        except Exception as e:
            logger.error(f"Redis connection test failed for db {db} after all retries: {e}")
            return False
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute Redis operation with retry logic."""
        return self._retry_handler.retry_with_backoff(func, *args, **kwargs)
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get optimized Django cache configuration."""
        base_location = f"redis://{self.redis_host}:{self.redis_port}"
        if self.redis_password:
            base_location = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        
        # SSL URL scheme
        if self.redis_ssl:
            base_location = base_location.replace("redis://", "rediss://")
        
        connection_pool_kwargs = {
            'max_connections': self.max_connections,
            'retry_on_timeout': True,
            'retry_on_error': [redis.ConnectionError, redis.TimeoutError],
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.connection_timeout,
            'socket_keepalive': self.socket_keepalive,
            'socket_keepalive_options': self.socket_keepalive_options,
            'health_check_interval': self.health_check_interval,
            'connection_class': self._get_connection_class()
        }
        
        # Add SSL parameters for django-redis
        ssl_kwargs = self._get_ssl_kwargs()
        connection_pool_kwargs.update(ssl_kwargs)
        
        return {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{base_location}/1",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': connection_pool_kwargs,
                    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                    'IGNORE_EXCEPTIONS': True,
                    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                },
                'KEY_PREFIX': 'trojan_defender',
                'VERSION': 1,
                'TIMEOUT': 300,
            },
            'sessions': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{base_location}/2",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': {
                        **connection_pool_kwargs,
                        'max_connections': min(50, self.max_connections)
                    },
                    'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
                },
                'KEY_PREFIX': 'sessions',
                'TIMEOUT': 86400,  # 24 hours
            },
            'rate_limit': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{base_location}/3",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': {
                        **connection_pool_kwargs,
                        'max_connections': min(30, self.max_connections)
                    },
                },
                'KEY_PREFIX': 'rate_limit',
                'TIMEOUT': 3600,  # 1 hour
            }
        }
    
    def cleanup_connections(self):
        """Clean up connection pools with proper error handling."""
        for pool_key, pool in list(self._connection_pools.items()):
            try:
                pool.disconnect()
                logger.info(f"Successfully disconnected Redis pool: {pool_key}")
            except Exception as e:
                logger.warning(f"Error disconnecting Redis pool {pool_key}: {e}")
        
        self._connection_pools.clear()
        
        # Clean up sentinel connection
        if self._sentinel:
            try:
                # Sentinel doesn't have a direct disconnect method, but we can clear it
                self._sentinel = None
                logger.info("Cleared Redis Sentinel connection")
            except Exception as e:
                logger.warning(f"Error clearing Redis Sentinel: {e}")


class RedisHealthMonitor:
    """Monitor Redis health and performance metrics."""
    
    def __init__(self, redis_config: OptimizedRedisConfig):
        self.redis_config = redis_config
        self.logger = logging.getLogger(f"{__name__}.HealthMonitor")
    
    def check_health(self) -> Dict[str, Any]:
        """Comprehensive Redis health check."""
        health_status = {
            'overall_status': 'healthy',
            'databases': {},
            'connection_pools': {},
            'performance_metrics': {}
        }
        
        # Check each database
        for db in [0, 1, 2, 3]:  # Default, cache, sessions, rate_limit
            try:
                client = self.redis_config.get_redis_client(db)
                
                # Basic connectivity
                start_time = time.time()
                client.ping()
                ping_time = (time.time() - start_time) * 1000  # ms
                
                # Get info
                info = client.info()
                
                health_status['databases'][f'db_{db}'] = {
                    'status': 'healthy',
                    'ping_time_ms': round(ping_time, 2),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
                
                # Calculate hit ratio
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                if hits + misses > 0:
                    hit_ratio = hits / (hits + misses) * 100
                    health_status['databases'][f'db_{db}']['hit_ratio_percent'] = round(hit_ratio, 2)
                
            except Exception as e:
                health_status['databases'][f'db_{db}'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
        
        # Check connection pools
        for pool_key, pool in self.redis_config._connection_pools.items():
            try:
                health_status['connection_pools'][pool_key] = {
                    'created_connections': pool.created_connections,
                    'available_connections': len(pool._available_connections),
                    'in_use_connections': len(pool._in_use_connections)
                }
            except Exception as e:
                health_status['connection_pools'][pool_key] = {
                    'error': str(e)
                }
        
        return health_status
    
    def log_health_status(self):
        """Log current health status."""
        try:
            health = self.check_health()
            if health['overall_status'] == 'healthy':
                self.logger.info("Redis health check passed")
            else:
                self.logger.warning(f"Redis health check issues detected: {health}")
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")


# Global instances
redis_config = OptimizedRedisConfig()
health_monitor = RedisHealthMonitor(redis_config)


def get_optimized_redis_client(db: int = 0) -> redis.Redis:
    """Get an optimized Redis client instance."""
    return redis_config.get_redis_client(db)


def test_redis_connection() -> bool:
    """Test Redis connection health."""
    return redis_config.test_connection()


def get_redis_health_status() -> Dict[str, Any]:
    """Get comprehensive Redis health status."""
    return health_monitor.check_health()