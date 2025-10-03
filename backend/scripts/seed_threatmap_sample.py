import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Ensure project root (backend) is in sys.path so 'trojan_defender' is importable
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trojan_defender.settings")
    django.setup()

    from django.contrib.auth import get_user_model
    from threatmap.models import ThreatEvent

    User = get_user_model()
    try:
        user = User.objects.get(id=2)
    except User.DoesNotExist:
        user = None

    # Create multiple sample threat map events across severities, countries, and timestamps
    sample_events = [
        {
            'threat_type': 'malware',
            'severity': 'low',
            'ip_address': '203.0.113.11',
            'country': 'US',
            'city': 'San Francisco',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'description': 'Low severity malware',
            'file_name': 'low.exe',
            'file_hash': 'a' * 64,
            'days_ago': 0,
        },
        {
            'threat_type': 'virus',
            'severity': 'medium',
            'ip_address': '198.51.100.12',
            'country': 'GB',
            'city': 'London',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'description': 'Medium severity virus',
            'file_name': 'medium.exe',
            'file_hash': 'b' * 64,
            'days_ago': 2,
        },
        {
            'threat_type': 'trojan',
            'severity': 'high',
            'ip_address': '192.0.2.13',
            'country': 'DE',
            'city': 'Berlin',
            'latitude': 52.52,
            'longitude': 13.405,
            'description': 'High severity trojan',
            'file_name': 'high.exe',
            'file_hash': 'c' * 64,
            'days_ago': 7,
        },
        {
            'threat_type': 'ransomware',
            'severity': 'critical',
            'ip_address': '203.0.113.14',
            'country': 'JP',
            'city': 'Tokyo',
            'latitude': 35.6762,
            'longitude': 139.6503,
            'description': 'Critical ransomware',
            'file_name': 'critical.exe',
            'file_hash': 'd' * 64,
            'days_ago': 14,
        },
        {
            'threat_type': 'spyware',
            'severity': 'medium',
            'ip_address': '198.51.100.15',
            'country': 'BR',
            'city': 'São Paulo',
            'latitude': -23.5505,
            'longitude': -46.6333,
            'description': 'Spyware activity',
            'file_name': 'spyware.exe',
            'file_hash': 'e' * 64,
            'days_ago': 21,
        },
        {
            'threat_type': 'worm',
            'severity': 'high',
            'ip_address': '192.0.2.16',
            'country': 'US',
            'city': 'New York',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'description': 'Worm propagation',
            'file_name': 'worm.exe',
            'file_hash': 'f' * 64,
            'days_ago': 28,
        },
    ]

    created_ids = []
    for ev in sample_events:
        event = ThreatEvent.objects.create(
            user=user,
            scan_result=None,
            threat_type=ev['threat_type'],
            severity=ev['severity'],
            ip_address=ev['ip_address'],
            country=ev['country'],
            city=ev['city'],
            latitude=ev['latitude'],
            longitude=ev['longitude'],
            description=ev['description'],
            file_name=ev['file_name'],
            file_hash=ev['file_hash'],
        )
        # Adjust timestamp to simulate past events
        if ev.get('days_ago'):
            event.timestamp = timezone.now() - timedelta(days=ev['days_ago'])
            event.save(update_fields=['timestamp'])
        created_ids.append(str(event.id))

    print(f"Created {len(created_ids)} ThreatMap events: {', '.join(created_ids)} for user_id={user.id if user else None}")


if __name__ == "__main__":
    main()