import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .external_api import ThreatIntelligenceUpdater
from .models import ThreatStatistics

logger = logging.getLogger(__name__)


class ThreatDataScheduler:
    """Scheduler for threat intelligence data updates"""
    
    def __init__(self):
        self.updater = ThreatIntelligenceUpdater()
        self.last_update = None
        self.update_interval = getattr(settings, 'THREAT_UPDATE_INTERVAL', 3600)  # 1 hour default
    
    def should_update(self):
        """Check if data should be updated based on interval"""
        if not self.last_update:
            return True
        
        time_since_update = (timezone.now() - self.last_update).total_seconds()
        return time_since_update >= self.update_interval
    
    def update_threat_data(self):
        """Update threat intelligence data from external APIs"""
        try:
            logger.info("Starting scheduled threat data update")
            
            # Check if we should update
            if not self.should_update():
                logger.info("Skipping update - too soon since last update")
                return False
            
            # Update from AbuseIPDB
            success = self.updater.update_from_abuseipdb_blacklist()
            
            if success:
                # Update daily statistics
                self.updater.update_daily_statistics()
                self.last_update = timezone.now()
                
                logger.info("Successfully completed scheduled threat data update")
                return True
            else:
                logger.error("Failed to update threat data from AbuseIPDB")
                return False
                
        except Exception as e:
            logger.error(f"Error in scheduled threat data update: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep=30):
        """Clean up old threat intelligence data"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days_to_keep)
            
            # Clean up old statistics
            deleted_stats = ThreatStatistics.objects.filter(
                date__lt=cutoff_date.date()
            ).delete()
            
            logger.info(f"Cleaned up {deleted_stats[0]} old statistics records")
            
            # Note: We keep ThreatIntelligence and ThreatEvent data longer
            # as they might be referenced for historical analysis
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# Global scheduler instance
threat_scheduler = ThreatDataScheduler()


def run_threat_update():
    """Function to be called by external schedulers (cron, celery, etc.)"""
    return threat_scheduler.update_threat_data()


def run_data_cleanup():
    """Function to clean up old data"""
    return threat_scheduler.cleanup_old_data()


# Simple in-memory scheduler for development
import threading
import time


class SimpleScheduler:
    """Simple in-memory scheduler for development purposes"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Started threat data scheduler")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Stopped threat data scheduler")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Update threat data every hour
                run_threat_update()
                
                # Clean up old data once per day
                current_hour = datetime.now().hour
                if current_hour == 2:  # Run cleanup at 2 AM
                    run_data_cleanup()
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(300)  # Sleep 5 minutes on error


# Global scheduler instance for development
simple_scheduler = SimpleScheduler()


def start_scheduler():
    """Start the simple scheduler (for development)"""
    simple_scheduler.start()


def stop_scheduler():
    """Stop the simple scheduler"""
    simple_scheduler.stop()