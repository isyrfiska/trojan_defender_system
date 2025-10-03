import logging
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.conf import settings
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ThreatEvent, GlobalThreatStats
from .serializers import ThreatEventSerializer
from scanner.models import ScanResult

logger = logging.getLogger('threatmap')
channel_layer = get_channel_layer()


@shared_task(bind=True, max_retries=3)
def process_threat_intelligence_feed(self, feed_url=None, feed_type='json'):
    """
    Process external threat intelligence feeds and create threat events.
    
    Args:
        feed_url (str): URL of the threat intelligence feed
        feed_type (str): Type of feed (json, xml, csv)
    
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Starting threat intelligence feed processing: {feed_url}")
        
        # Default feeds if none provided
        if not feed_url:
            feed_url = getattr(settings, 'DEFAULT_THREAT_FEED_URL', None)
            if not feed_url:
                logger.warning("No threat intelligence feed URL configured")
                return {'success': False, 'error': 'No feed URL configured'}
        
        # Fetch feed data
        try:
            response = requests.get(
                feed_url,
                timeout=30,
                headers={'User-Agent': 'TrojanDefender/1.0'}
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch threat feed: {str(e)}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        # Parse feed data based on type
        if feed_type == 'json':
            feed_data = response.json()
        else:
            logger.error(f"Unsupported feed type: {feed_type}")
            return {'success': False, 'error': f'Unsupported feed type: {feed_type}'}
        
        # Process and validate threat data
        processed_count = 0
        errors = []
        
        with transaction.atomic():
            for item in feed_data.get('threats', []):
                try:
                    # Validate and sanitize threat data
                    threat_data = validate_threat_data(item)
                    if not threat_data:
                        continue
                    
                    # Check for duplicates
                    if ThreatEvent.objects.filter(
                        ip_address=threat_data.get('ip_address'),
                        file_hash=threat_data.get('file_hash'),
                        timestamp__gte=timezone.now() - timedelta(hours=24)
                    ).exists():
                        continue
                    
                    # Create threat event
                    threat_event = ThreatEvent.objects.create(**threat_data)
                    processed_count += 1
                    
                    # Send real-time update
                    send_threat_update(threat_event)
                    
                except Exception as e:
                    errors.append(f"Error processing threat item: {str(e)}")
                    logger.error(f"Error processing threat item: {str(e)}")
        
        logger.info(f"Processed {processed_count} threat events from feed")
        
        # Update global statistics
        update_global_threat_stats.delay()
        
        return {
            'success': True,
            'processed_count': processed_count,
            'errors': errors[:10]  # Limit error list
        }
        
    except Exception as e:
        logger.error(f"Error in threat intelligence processing: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def process_scan_results_to_threats():
    """
    Convert recent scan results to threat events for the threat map.
    
    Returns:
        dict: Processing results
    """
    try:
        logger.info("Processing scan results to threat events")
        
        # Get recent scan results with threats
        since = timezone.now() - timedelta(hours=1)
        scan_results = ScanResult.objects.filter(
            scan_date__gte=since,
            threat_level__in=['medium', 'high', 'critical'],
            threats__isnull=False
        ).distinct()
        
        processed_count = 0
        
        for scan_result in scan_results:
            try:
                # Check if threat event already exists for this scan
                if ThreatEvent.objects.filter(scan_result=scan_result).exists():
                    continue
                
                # Get geolocation data (mock implementation)
                geo_data = get_geolocation_data(scan_result.user)
                
                # Create threat event from scan result
                threat_event = ThreatEvent.objects.create(
                    user=scan_result.user,
                    scan_result=scan_result,
                    threat_type=determine_threat_type(scan_result),
                    severity=map_threat_level_to_severity(scan_result.threat_level),
                    description=f"Threat detected in file: {scan_result.file_name}",
                    file_name=scan_result.file_name,
                    file_hash=scan_result.file_hash,
                    country=geo_data.get('country', ''),
                    city=geo_data.get('city', ''),
                    latitude=geo_data.get('latitude'),
                    longitude=geo_data.get('longitude'),
                )
                
                processed_count += 1
                
                # Send real-time update
                send_threat_update(threat_event)
                
            except Exception as e:
                logger.error(f"Error processing scan result {scan_result.id}: {str(e)}")
        
        logger.info(f"Processed {processed_count} scan results to threat events")
        
        return {
            'success': True,
            'processed_count': processed_count
        }
        
    except Exception as e:
        logger.error(f"Error processing scan results: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_global_threat_stats():
    """
    Update global threat statistics for the current date.
    
    Returns:
        dict: Update results
    """
    try:
        logger.info("Updating global threat statistics")
        
        today = timezone.now().date()
        
        # Get or create today's stats
        stats, created = GlobalThreatStats.objects.get_or_create(
            date=today,
            defaults={
                'total_threats': 0,
                'country_distribution': {}
            }
        )
        
        # Calculate statistics for today
        today_threats = ThreatEvent.objects.filter(
            timestamp__date=today
        )
        
        # Update counts
        stats.total_threats = today_threats.count()
        stats.malware_count = today_threats.filter(threat_type='malware').count()
        stats.virus_count = today_threats.filter(threat_type='virus').count()
        stats.ransomware_count = today_threats.filter(threat_type='ransomware').count()
        stats.trojan_count = today_threats.filter(threat_type='trojan').count()
        stats.spyware_count = today_threats.filter(threat_type='spyware').count()
        stats.adware_count = today_threats.filter(threat_type='adware').count()
        stats.worm_count = today_threats.filter(threat_type='worm').count()
        stats.rootkit_count = today_threats.filter(threat_type='rootkit').count()
        stats.backdoor_count = today_threats.filter(threat_type='backdoor').count()
        stats.exploit_count = today_threats.filter(threat_type='exploit').count()
        stats.other_count = today_threats.filter(threat_type='other').count()
        
        # Update severity counts
        stats.low_severity_count = today_threats.filter(severity='low').count()
        stats.medium_severity_count = today_threats.filter(severity='medium').count()
        stats.high_severity_count = today_threats.filter(severity='high').count()
        stats.critical_severity_count = today_threats.filter(severity='critical').count()
        
        # Update country distribution
        country_stats = {}
        for threat in today_threats.values('country').distinct():
            country = threat['country']
            if country:
                country_stats[country] = today_threats.filter(country=country).count()
        
        stats.country_distribution = country_stats
        stats.save()
        
        # Send global stats update via WebSocket
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "global_threat_stats",
                {
                    "type": "global_stats_update",
                    "stats_data": {
                        'date': today.isoformat(),
                        'total_threats': stats.total_threats,
                        'country_distribution': stats.country_distribution,
                        'severity_distribution': {
                            'low': stats.low_severity_count,
                            'medium': stats.medium_severity_count,
                            'high': stats.high_severity_count,
                            'critical': stats.critical_severity_count,
                        }
                    }
                }
            )
        
        logger.info(f"Updated global threat statistics: {stats.total_threats} threats")
        
        return {
            'success': True,
            'total_threats': stats.total_threats,
            'date': today.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating global threat stats: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_threat_events(days_to_keep=90):
    """
    Clean up old threat events to maintain database performance.
    
    Args:
        days_to_keep (int): Number of days of threat events to keep
    
    Returns:
        dict: Cleanup results
    """
    try:
        logger.info(f"Cleaning up threat events older than {days_to_keep} days")
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Delete old threat events
        deleted_count, _ = ThreatEvent.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        # Delete old global stats (keep 1 year)
        stats_cutoff = timezone.now().date() - timedelta(days=365)
        deleted_stats, _ = GlobalThreatStats.objects.filter(
            date__lt=stats_cutoff
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} threat events and {deleted_stats} stat records")
        
        return {
            'success': True,
            'deleted_threats': deleted_count,
            'deleted_stats': deleted_stats
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up threat events: {str(e)}")
        return {'success': False, 'error': str(e)}


def validate_threat_data(data):
    """
    Validate and sanitize threat data from external feeds.
    
    Args:
        data (dict): Raw threat data
    
    Returns:
        dict: Validated threat data or None if invalid
    """
    try:
        # Required fields
        if not data.get('threat_type') or not data.get('severity'):
            return None
        
        # Validate threat type
        valid_threat_types = [choice[0] for choice in ThreatEvent.ThreatType.choices]
        if data['threat_type'] not in valid_threat_types:
            data['threat_type'] = 'other'
        
        # Validate severity
        valid_severities = [choice[0] for choice in ThreatEvent.ThreatSeverity.choices]
        if data['severity'] not in valid_severities:
            data['severity'] = 'medium'
        
        # Sanitize strings
        for field in ['description', 'file_name', 'country', 'city']:
            if field in data and data[field]:
                data[field] = str(data[field])[:255]  # Limit length
        
        # Validate coordinates
        if 'latitude' in data:
            try:
                lat = float(data['latitude'])
                if -90 <= lat <= 90:
                    data['latitude'] = lat
                else:
                    data['latitude'] = None
            except (ValueError, TypeError):
                data['latitude'] = None
        
        if 'longitude' in data:
            try:
                lng = float(data['longitude'])
                if -180 <= lng <= 180:
                    data['longitude'] = lng
                else:
                    data['longitude'] = None
            except (ValueError, TypeError):
                data['longitude'] = None
        
        # Set timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = timezone.now()
        
        return data
        
    except Exception as e:
        logger.error(f"Error validating threat data: {str(e)}")
        return None


def send_threat_update(threat_event):
    """
    Send real-time threat update via WebSocket.
    
    Args:
        threat_event (ThreatEvent): The threat event to broadcast
    """
    try:
        if not channel_layer:
            return
        
        # Serialize threat data
        serializer = ThreatEventSerializer(threat_event)
        threat_data = serializer.data
        
        # Send to all connected users (could be filtered by user permissions)
        async_to_sync(channel_layer.group_send)(
            f"threat_map_{threat_event.user_id}",
            {
                "type": "threat_update",
                "threat_data": threat_data
            }
        )
        
        # Send critical threat alerts
        if threat_event.severity == 'critical':
            async_to_sync(channel_layer.group_send)(
                f"threat_map_{threat_event.user_id}",
                {
                    "type": "threat_alert",
                    "alert_data": {
                        'id': str(threat_event.id),
                        'threat_type': threat_event.threat_type,
                        'severity': threat_event.severity,
                        'country': threat_event.country,
                        'timestamp': threat_event.timestamp.isoformat()
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"Error sending threat update: {str(e)}")


def get_geolocation_data(user):
    """
    Get geolocation data for a user (mock implementation).
    In production, this would use IP geolocation services.
    
    Args:
        user: User object
    
    Returns:
        dict: Geolocation data
    """
    # Mock geolocation data
    # In production, you would use services like MaxMind GeoIP2
    return {
        'country': 'United States',
        'city': 'New York',
        'latitude': 40.7128,
        'longitude': -74.0060
    }


def determine_threat_type(scan_result):
    """
    Determine threat type from scan result.
    
    Args:
        scan_result (ScanResult): Scan result object
    
    Returns:
        str: Threat type
    """
    # Simple mapping based on file type and threats found
    if scan_result.threats.filter(threat_type='trojan').exists():
        return 'trojan'
    elif scan_result.threats.filter(threat_type='virus').exists():
        return 'virus'
    elif scan_result.threats.filter(threat_type='malware').exists():
        return 'malware'
    else:
        return 'other'


def map_threat_level_to_severity(threat_level):
    """
    Map scan result threat level to threat event severity.
    
    Args:
        threat_level (str): Threat level from scan result
    
    Returns:
        str: Severity level
    """
    mapping = {
        'clean': 'low',
        'low': 'low',
        'medium': 'medium',
        'high': 'high',
        'critical': 'critical'
    }
    return mapping.get(threat_level, 'medium')