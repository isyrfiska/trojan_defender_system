import logging
from .models import ThreatEvent, GlobalThreatStats

logger = logging.getLogger('api')

class ThreatMapService:
    """Service class for threat map operations"""
    
    @staticmethod
    def get_threat_map_data():
        """Get threat map data for visualization"""
        try:
            # Get all threat events with location data
            threat_events = ThreatEvent.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).order_by('-timestamp')[:1000]  # Limit to recent 1000 events
            
            return threat_events
        except Exception as e:
            logger.error(f"Error retrieving threat map data: {str(e)}")
            return []
    
    @staticmethod
    def get_global_threat_stats():
        """Get global threat statistics"""
        try:
            stats, created = GlobalThreatStats.objects.get_or_create(id=1)
            return stats
        except Exception as e:
            logger.error(f"Error retrieving global threat stats: {str(e)}")
            return None