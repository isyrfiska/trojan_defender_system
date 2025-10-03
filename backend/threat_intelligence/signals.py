from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .models import ThreatIntelligence, ThreatEvent, ThreatStatistics

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=ThreatIntelligence)
def threat_intelligence_updated(sender, instance, created, **kwargs):
    """Broadcast threat intelligence updates via WebSocket."""
    try:
        if channel_layer:
            # Prepare the data to broadcast
            threat_data = {
                'id': instance.id,
                'ip_address': instance.ip_address,
                'country': instance.country_name or instance.country_code,
                'confidence_percentage': instance.confidence_percentage,
                'abuse_confidence': instance.abuse_confidence,
                'last_reported_at': instance.last_reported_at.isoformat() if instance.last_reported_at else None,
                'created_at': instance.created_at.isoformat(),
                'updated_at': instance.updated_at.isoformat(),
                'action': 'created' if created else 'updated'
            }
            
            # Broadcast to threat intelligence WebSocket group
            async_to_sync(channel_layer.group_send)(
                'threat_intelligence',
                {
                    'type': 'threat_update',
                    'data': threat_data
                }
            )
            
            logger.info(f"Broadcasted threat intelligence update for IP {instance.ip_address}")
            
    except Exception as e:
        logger.error(f"Failed to broadcast threat intelligence update: {e}")


@receiver(post_save, sender=ThreatEvent)
def threat_event_created(sender, instance, created, **kwargs):
    """Broadcast new threat events via WebSocket."""
    if not created:
        return
        
    try:
        if channel_layer:
            # Prepare the event data to broadcast
            event_data = {
                'id': instance.id,
                'threat_intelligence_id': instance.threat_intelligence.id,
                'ip_address': instance.threat_intelligence.ip_address,
                'country': instance.threat_intelligence.country_name or instance.threat_intelligence.country_code,
                'event_type': instance.event_type,
                'severity': instance.severity,
                'description': instance.description,
                'created_at': instance.created_at.isoformat(),
                'confidence': instance.threat_intelligence.confidence_percentage
            }
            
            # Broadcast to threat intelligence WebSocket group
            async_to_sync(channel_layer.group_send)(
                'threat_intelligence',
                {
                    'type': 'new_threat_event',
                    'data': event_data
                }
            )
            
            logger.info(f"Broadcasted new threat event for IP {instance.threat_intelligence.ip_address}")
            
    except Exception as e:
        logger.error(f"Failed to broadcast threat event: {e}")


@receiver(post_save, sender=ThreatStatistics)
def daily_stats_updated(sender, instance, created, **kwargs):
    """Broadcast daily statistics updates via WebSocket."""
    try:
        if channel_layer:
            # Prepare the stats data to broadcast
            stats_data = {
                'date': instance.date.isoformat(),
                'new_threats': instance.new_threats,
                'total_threats': instance.total_threats,
                'high_confidence_threats': instance.high_confidence_threats,
                'updated_at': instance.updated_at.isoformat(),
                'action': 'created' if created else 'updated'
            }
            
            # Broadcast to threat intelligence WebSocket group
            async_to_sync(channel_layer.group_send)(
                'threat_intelligence',
                {
                    'type': 'stats_update',
                    'data': stats_data
                }
            )
            
            logger.info(f"Broadcasted daily stats update for {instance.date}")
            
    except Exception as e:
        logger.error(f"Failed to broadcast daily stats update: {e}")


def broadcast_threat_stats():
    """Utility function to manually broadcast current threat statistics."""
    try:
        if channel_layer:
            from django.utils import timezone
            from datetime import timedelta
            
            # Get current statistics
            today = timezone.now().date()
            today_stats = DailyThreatStats.objects.filter(date=today).first()
            
            total_threats = ThreatIntelligence.objects.count()
            total_events = ThreatEvent.objects.count()
            
            # Get recent activity (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_events = ThreatEvent.objects.filter(
                created_at__gte=yesterday
            ).count()
            
            # Get threat severity distribution
            severity_counts = {}
            for severity in ['low', 'medium', 'high', 'critical']:
                count = ThreatIntelligence.objects.filter(
                    threat_level=severity
                ).count()
                severity_counts[severity] = count
            
            stats_data = {
                'total_threats': total_threats,
                'total_events': total_events,
                'recent_events_24h': recent_events,
                'today_stats': {
                    'new_threats': today_stats.new_threats if today_stats else 0,
                    'updated_threats': today_stats.updated_threats if today_stats else 0,
                    'total_events': today_stats.total_events if today_stats else 0,
                } if today_stats else None,
                'severity_distribution': severity_counts,
                'last_updated': timezone.now().isoformat()
            }
            
            # Broadcast to threat intelligence WebSocket group
            async_to_sync(channel_layer.group_send)(
                'threat_intelligence',
                {
                    'type': 'stats_update',
                    'data': stats_data
                }
            )
            
            logger.info("Broadcasted current threat statistics")
            
    except Exception as e:
        logger.error(f"Failed to broadcast threat statistics: {e}")