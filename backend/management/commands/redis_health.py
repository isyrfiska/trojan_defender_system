"""
Redis Health Check Management Command
Provides health monitoring and maintenance utilities for Redis connections.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import time
from trojan_defender.redis_config import health_monitor, redis_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor Redis health and performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuous health monitoring',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Health check interval in seconds (default: 30)',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up Redis connections',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test Redis connection',
        )

    def handle(self, *args, **options):
        if options['cleanup']:
            self.cleanup_connections()
        elif options['test_connection']:
            self.test_connection()
        elif options['continuous']:
            self.continuous_monitoring(options['interval'])
        else:
            self.single_health_check()

    def cleanup_connections(self):
        """Clean up Redis connections."""
        self.stdout.write("Cleaning up Redis connections...")
        try:
            redis_config.cleanup_connections()
            self.stdout.write(
                self.style.SUCCESS("Redis connections cleaned up successfully")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to clean up connections: {e}")
            )

    def test_connection(self):
        """Test Redis connection."""
        self.stdout.write("Testing Redis connection...")
        try:
            if redis_config.test_connection():
                self.stdout.write(
                    self.style.SUCCESS("Redis connection test passed")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Redis connection test failed")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Connection test error: {e}")
            )

    def single_health_check(self):
        """Perform a single health check."""
        self.stdout.write("Performing Redis health check...")
        try:
            health_status = health_monitor.check_health()
            self.display_health_status(health_status)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Health check failed: {e}")
            )

    def continuous_monitoring(self, interval):
        """Run continuous health monitoring."""
        self.stdout.write(
            f"Starting continuous Redis monitoring (interval: {interval}s)"
        )
        self.stdout.write("Press Ctrl+C to stop...")
        
        try:
            while True:
                health_status = health_monitor.check_health()
                self.display_health_status(health_status, compact=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped.")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Monitoring error: {e}")
            )

    def display_health_status(self, health_status, compact=False):
        """Display health status information."""
        overall_status = health_status.get('overall_status', 'unknown')
        
        if overall_status == 'healthy':
            status_style = self.style.SUCCESS
        elif overall_status == 'degraded':
            status_style = self.style.WARNING
        else:
            status_style = self.style.ERROR

        if compact:
            self.stdout.write(
                f"[{time.strftime('%H:%M:%S')}] "
                f"Status: {status_style(overall_status.upper())}"
            )
        else:
            self.stdout.write(f"\nOverall Status: {status_style(overall_status.upper())}")
            
            # Database status
            databases = health_status.get('databases', {})
            if databases:
                self.stdout.write("\nDatabase Status:")
                for db_name, db_info in databases.items():
                    db_status = db_info.get('status', 'unknown')
                    if db_status == 'healthy':
                        db_style = self.style.SUCCESS
                    else:
                        db_style = self.style.ERROR
                    
                    self.stdout.write(f"  {db_name}: {db_style(db_status)}")
                    
                    if db_status == 'healthy':
                        ping_time = db_info.get('ping_time_ms', 'N/A')
                        hit_ratio = db_info.get('hit_ratio_percent', 'N/A')
                        self.stdout.write(f"    Ping: {ping_time}ms, Hit Ratio: {hit_ratio}%")
                    else:
                        error = db_info.get('error', 'Unknown error')
                        self.stdout.write(f"    Error: {error}")
            
            # Connection pool status
            pools = health_status.get('connection_pools', {})
            if pools:
                self.stdout.write("\nConnection Pools:")
                for pool_name, pool_info in pools.items():
                    if 'error' in pool_info:
                        self.stdout.write(f"  {pool_name}: {self.style.ERROR('ERROR')}")
                        self.stdout.write(f"    {pool_info['error']}")
                    else:
                        created = pool_info.get('created_connections', 0)
                        available = pool_info.get('available_connections', 0)
                        in_use = pool_info.get('in_use_connections', 0)
                        self.stdout.write(f"  {pool_name}: Created={created}, Available={available}, In Use={in_use}")