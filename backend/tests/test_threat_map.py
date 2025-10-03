from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from threatmap.models import ThreatEvent, GlobalThreatStats

User = get_user_model()


class ThreatEventModelTest(TestCase):
    """Test cases for ThreatEvent model."""
    
    def test_threat_event_creation(self):
        """Test creating a threat event instance."""
        event = ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            city='New York',
            latitude=40.7128,
            longitude=-74.0060,
            description='Malware detected in network traffic'
        )
        
        self.assertEqual(event.threat_type, 'malware')
        self.assertEqual(event.severity, 'high')
        self.assertEqual(event.ip_address, '192.168.1.100')
        self.assertEqual(event.country, 'US')
        self.assertEqual(event.city, 'New York')
        self.assertEqual(float(event.latitude), 40.7128)
        self.assertEqual(float(event.longitude), -74.0060)
        self.assertIsNotNone(event.timestamp)
    
    def test_threat_event_str_representation(self):
        """Test string representation of threat event."""
        event = ThreatEvent.objects.create(
            threat_type='phishing',
            severity='medium',
            ip_address='10.0.0.1',
            country='CA',
            city='Toronto',
            description='Phishing attempt detected'
        )
        
        expected_str = f"phishing - medium (10.0.0.1)"
        self.assertEqual(str(event), expected_str)
    
    def test_threat_event_type_choices(self):
        """Test threat event type choices."""
        valid_types = ['malware', 'phishing', 'ddos', 'intrusion', 'spam', 'other']
        
        for threat_type in valid_types:
            event = ThreatEvent.objects.create(
                threat_type=threat_type,
                severity='medium',
                ip_address='192.168.1.1',
                country='US',
                description=f'Test {threat_type} event'
            )
            self.assertEqual(event.threat_type, threat_type)
    
    def test_threat_event_severity_choices(self):
        """Test threat event severity choices."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        
        for severity in valid_severities:
            event = ThreatEvent.objects.create(
                threat_type='malware',
                severity=severity,
                ip_address='192.168.1.1',
                country='US',
                description=f'Test {severity} severity event'
            )
            self.assertEqual(event.severity, severity)
    
    def test_threat_event_ordering(self):
        """Test threat event ordering by timestamp."""
        event1 = ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.1',
            country='US',
            description='First event'
        )
        
        event2 = ThreatEvent.objects.create(
            threat_type='phishing',
            severity='medium',
            ip_address='192.168.1.2',
            country='CA',
            description='Second event'
        )
        
        events = ThreatEvent.objects.all()
        
        # Should be ordered by timestamp descending
        self.assertEqual(events.first(), event2)
        self.assertEqual(events.last(), event1)
    
    def test_threat_event_location_data(self):
        """Test threat event with location data."""
        event = ThreatEvent.objects.create(
            threat_type='ddos',
            severity='critical',
            ip_address='203.0.113.1',
            country='GB',
            city='London',
            latitude=51.5074,
            longitude=-0.1278,
            description='DDoS attack from London'
        )
        
        self.assertEqual(event.country, 'GB')
        self.assertEqual(event.city, 'London')
        self.assertIsNotNone(event.latitude)
        self.assertIsNotNone(event.longitude)


class GlobalThreatStatsModelTest(TestCase):
    """Test cases for GlobalThreatStats model."""
    
    def test_global_threat_stats_creation(self):
        """Test creating global threat statistics."""
        stats = GlobalThreatStats.objects.create(
            total_threats=1000,
            active_threats=250,
            resolved_threats=750,
            high_severity_threats=100,
            medium_severity_threats=400,
            low_severity_threats=500
        )
        
        self.assertEqual(stats.total_threats, 1000)
        self.assertEqual(stats.active_threats, 250)
        self.assertEqual(stats.resolved_threats, 750)
        self.assertEqual(stats.high_severity_threats, 100)
        self.assertEqual(stats.medium_severity_threats, 400)
        self.assertEqual(stats.low_severity_threats, 500)
        self.assertIsNotNone(stats.last_updated)
    
    def test_global_threat_stats_str_representation(self):
        """Test string representation of global threat stats."""
        stats = GlobalThreatStats.objects.create(
            total_threats=500,
            active_threats=100,
            resolved_threats=400
        )
        
        expected_str = f"Global Stats - Total: 500, Active: 100"
        self.assertEqual(str(stats), expected_str)
    
    def test_global_threat_stats_calculations(self):
        """Test calculated properties of global threat stats."""
        stats = GlobalThreatStats.objects.create(
            total_threats=1000,
            active_threats=200,
            resolved_threats=800,
            high_severity_threats=150,
            medium_severity_threats=350,
            low_severity_threats=500
        )
        
        # Test that totals add up correctly
        severity_total = stats.high_severity_threats + stats.medium_severity_threats + stats.low_severity_threats
        self.assertEqual(severity_total, stats.total_threats)
        
        status_total = stats.active_threats + stats.resolved_threats
        self.assertEqual(status_total, stats.total_threats)


class ThreatMapIntegrationTest(TestCase):
    """Test cases for threat map integration functionality."""
    
    def setUp(self):
        # Create test threat events
        self.events = []
        
        # Create events from different countries
        countries_data = [
            ('US', 'New York', 40.7128, -74.0060, 'malware'),
            ('CA', 'Toronto', 43.6532, -79.3832, 'phishing'),
            ('GB', 'London', 51.5074, -0.1278, 'ddos'),
            ('DE', 'Berlin', 52.5200, 13.4050, 'intrusion'),
            ('JP', 'Tokyo', 35.6762, 139.6503, 'spam')
        ]
        
        for country, city, lat, lng, threat_type in countries_data:
            event = ThreatEvent.objects.create(
                threat_type=threat_type,
                severity='medium',
                ip_address=f'192.168.1.{len(self.events) + 1}',
                country=country,
                city=city,
                latitude=lat,
                longitude=lng,
                description=f'{threat_type} from {city}'
            )
            self.events.append(event)
        
        # Create global stats
        self.global_stats = GlobalThreatStats.objects.create(
            total_threats=len(self.events),
            active_threats=3,
            resolved_threats=2,
            high_severity_threats=1,
            medium_severity_threats=4,
            low_severity_threats=0
        )
    
    def test_threat_events_by_country(self):
        """Test grouping threat events by country."""
        countries = ThreatEvent.objects.values_list('country', flat=True).distinct()
        
        self.assertEqual(len(countries), 5)
        self.assertIn('US', countries)
        self.assertIn('CA', countries)
        self.assertIn('GB', countries)
        self.assertIn('DE', countries)
        self.assertIn('JP', countries)
    
    def test_threat_events_by_type(self):
        """Test grouping threat events by type."""
        threat_types = ThreatEvent.objects.values_list('threat_type', flat=True).distinct()
        
        self.assertEqual(len(threat_types), 5)
        self.assertIn('malware', threat_types)
        self.assertIn('phishing', threat_types)
        self.assertIn('ddos', threat_types)
        self.assertIn('intrusion', threat_types)
        self.assertIn('spam', threat_types)
    
    def test_recent_threat_events(self):
        """Test filtering recent threat events."""
        recent_events = ThreatEvent.objects.filter(
            timestamp__gte=datetime.now() - timedelta(hours=24)
        )
        
        self.assertEqual(recent_events.count(), 5)
    
    def test_high_severity_threats(self):
        """Test filtering high severity threats."""
        # Create a high severity threat
        high_severity_event = ThreatEvent.objects.create(
            threat_type='malware',
            severity='critical',
            ip_address='192.168.1.100',
            country='RU',
            city='Moscow',
            description='Critical malware attack'
        )
        
        high_severity_threats = ThreatEvent.objects.filter(
            severity__in=['high', 'critical']
        )
        
        self.assertEqual(high_severity_threats.count(), 1)
        self.assertEqual(high_severity_threats.first(), high_severity_event)
    
    def test_threat_map_data_structure(self):
        """Test threat map data structure for frontend."""
        threat_data = []
        
        for event in ThreatEvent.objects.all():
            threat_data.append({
                'id': event.id,
                'type': event.threat_type,
                'severity': event.severity,
                'location': {
                    'country': event.country,
                    'city': event.city,
                    'coordinates': [float(event.longitude), float(event.latitude)]
                },
                'timestamp': event.timestamp.isoformat(),
                'description': event.description
            })
        
        self.assertEqual(len(threat_data), 5)
        
        # Verify data structure
        for item in threat_data:
            self.assertIn('id', item)
            self.assertIn('type', item)
            self.assertIn('severity', item)
            self.assertIn('location', item)
            self.assertIn('timestamp', item)
            self.assertIn('coordinates', item['location'])
            self.assertEqual(len(item['location']['coordinates']), 2)


class ThreatMapAPITest(APITestCase):
    """Test cases for ThreatMap API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test threat events
        self.threat_event = ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            city='New York',
            latitude=40.7128,
            longitude=-74.0060,
            description='Test malware event'
        )
        
        # Create global stats
        self.global_stats = GlobalThreatStats.objects.create(
            total_threats=100,
            active_threats=25,
            resolved_threats=75,
            high_severity_threats=10,
            medium_severity_threats=40,
            low_severity_threats=50
        )
    
    def test_get_threat_events(self):
        """Test retrieving threat events via API."""
        response = self.client.get('/api/threatmap/events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        
        event_data = response.data[0]
        self.assertEqual(event_data['threat_type'], 'malware')
        self.assertEqual(event_data['severity'], 'high')
        self.assertEqual(event_data['country'], 'US')
    
    def test_get_threat_events_filtered_by_country(self):
        """Test filtering threat events by country."""
        # Create event from different country
        ThreatEvent.objects.create(
            threat_type='phishing',
            severity='medium',
            ip_address='10.0.0.1',
            country='CA',
            city='Toronto',
            description='Canadian phishing event'
        )
        
        response = self.client.get('/api/threatmap/events/?country=US')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['country'], 'US')
    
    def test_get_threat_events_filtered_by_type(self):
        """Test filtering threat events by type."""
        response = self.client.get('/api/threatmap/events/?threat_type=malware')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['threat_type'], 'malware')
    
    def test_get_threat_events_filtered_by_severity(self):
        """Test filtering threat events by severity."""
        response = self.client.get('/api/threatmap/events/?severity=high')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['severity'], 'high')
    
    def test_get_global_threat_stats(self):
        """Test retrieving global threat statistics."""
        response = self.client.get('/api/threatmap/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_threats'], 100)
        self.assertEqual(response.data['active_threats'], 25)
        self.assertEqual(response.data['resolved_threats'], 75)
    
    def test_get_threat_events_recent(self):
        """Test retrieving recent threat events."""
        response = self.client.get('/api/threatmap/events/recent/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to threat map endpoints."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/threatmap/events/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_threat_event_detail(self):
        """Test retrieving threat event details."""
        response = self.client.get(f'/api/threatmap/events/{self.threat_event.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.threat_event.id)
        self.assertEqual(response.data['threat_type'], 'malware')
        self.assertEqual(response.data['description'], 'Test malware event')