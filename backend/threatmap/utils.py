import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


def get_geolocation(ip_address):
    """Get geolocation data for an IP address using a third-party service."""
    try:
        # Use a free IP geolocation API (replace with your preferred service)
        response = requests.get(f"https://ipapi.co/{ip_address}/json/")
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country_name'),
                'country_code': data.get('country_code'),
                'city': data.get('city'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }
    except Exception as e:
        logger.error(f"Error getting geolocation data: {str(e)}")
    
    # Return default values if geolocation fails
    return {
        'country': 'Unknown',
        'country_code': 'XX',
        'city': 'Unknown',
        'latitude': 0,
        'longitude': 0,
    }


def broadcast_threat_event(threat_event):
    """Broadcast a new threat event to all connected WebSocket clients."""
    try:
        channel_layer = get_channel_layer()
        
        # Prepare the data to send
        data = {
            'id': str(threat_event.id),
            'threat_type': threat_event.get_threat_type_display(),
            'severity': threat_event.get_severity_display(),
            'country': threat_event.country,
            'country_code': threat_event.country_code,
            'city': threat_event.city,
            'latitude': float(threat_event.latitude) if threat_event.latitude else 0,
            'longitude': float(threat_event.longitude) if threat_event.longitude else 0,
            'timestamp': threat_event.timestamp.isoformat(),
        }
        
        # Send to the threat_map group
        async_to_sync(channel_layer.group_send)(
            'threat_map',
            {
                'type': 'send_threat_update',
                'data': data
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Error broadcasting threat event: {str(e)}")
        return False