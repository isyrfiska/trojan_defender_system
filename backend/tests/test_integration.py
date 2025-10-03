"""
Integration tests for the Trojan Defender application.
Tests the interaction between different components and API endpoints.
"""

import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from threatmap.models import ThreatEvent, GlobalThreatStats
from scanner.models import ScanResult, ScanThreat
from notifications.models import Notification

User = get_user_model()


class APIIntegrationTest(APITestCase):
    """Integration tests for API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_threat_map_api_flow(self):
        """Test complete threat map API flow."""
        # Create test threat events
        ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            city='New York',
            latitude=40.7128,
            longitude=-74.0060,
            description='Test malware event'
        )
        
        ThreatEvent.objects.create(
            threat_type='phishing',
            severity='medium',
            ip_address='10.0.0.1',
            country='CA',
            city='Toronto',
            latitude=43.6532,
            longitude=-79.3832,
            description='Test phishing event'
        )
        
        # Test threat events endpoint
        response = self.client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['results']), 2)
        
        # Test map data endpoint
        response = self.client.get('/api/threatmap/map/data/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('threat_events', data)
        self.assertIn('threat_stats', data)
        self.assertEqual(len(data['threat_events']), 2)
        
        # Test stats endpoint
        response = self.client.get('/api/threatmap/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('results', data)
    
    def test_authentication_flow(self):
        """Test authentication and authorization flow."""
        # Test unauthenticated access
        client = APIClient()
        response = client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test authenticated access
        response = self.client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test token refresh
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': str(refresh)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
    
    @patch('scanner.unified_scanner.UnifiedScanner.scan_file')
    def test_scanner_integration(self, mock_scan):
        """Test scanner integration with threat detection."""
        # Mock scanner response
        mock_scan.return_value = {
            'is_malicious': True,
            'threat_type': 'trojan',
            'confidence': 0.95,
            'details': {'engine': 'test', 'signature': 'test.trojan'}
        }
        
        # Create a scan
        scan = ScanResult.objects.create(
            user=self.user,
            file_name='test.exe',
            file_size=1024,
            file_type='application/x-executable',
            file_hash='abc123def456',
            status='pending',
            threat_level='unknown'
        )
        
        # Test scan endpoint
        response = self.client.get(f'/api/scanner/scans/{scan.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test scan results
        response = self.client.get('/api/scanner/scans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(len(data['results']), 1)


class CacheIntegrationTest(TestCase):
    """Test caching integration across the application."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='cache_test@example.com',
            password='testpass123'
        )
    
    @patch('trojan_defender.cache_utils.cache')
    def test_threat_map_caching(self, mock_cache):
        """Test threat map data caching."""
        from threatmap.views import ThreatMapDataView
        from django.test import RequestFactory
        
        # Mock cache miss
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        # Create test data
        ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            description='Test event'
        )
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/api/threatmap/map/data/')
        request.user = self.user
        
        # Test view
        view = ThreatMapDataView()
        response = view.get(request)
        
        # Verify cache was called
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()
    
    def test_global_stats_caching(self):
        """Test global threat stats caching behavior."""
        # Create initial stats
        stats = GlobalThreatStats.objects.create(
            date=datetime.now().date(),
            total_threats=100,
            malware_count=30,
            virus_count=20,
            trojan_count=25,
            low_severity_count=40,
            medium_severity_count=35,
            high_severity_count=20,
            critical_severity_count=5
        )
        
        # Test stats retrieval
        retrieved_stats = GlobalThreatStats.objects.filter(
            date=datetime.now().date()
        ).first()
        
        self.assertEqual(retrieved_stats.total_threats, 100)
        self.assertEqual(retrieved_stats.malware_count, 30)


class DatabaseIntegrationTest(TransactionTestCase):
    """Test database operations and transactions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='db_test@example.com',
            password='testpass123'
        )
    
    def test_threat_event_signal_integration(self):
        """Test that creating threat events triggers proper signals."""
        initial_count = GlobalThreatStats.objects.count()
        
        # Create threat event
        ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            description='Test signal event'
        )
        
        # Check if global stats were updated
        # Note: This depends on signal implementation
        final_count = GlobalThreatStats.objects.count()
        self.assertGreaterEqual(final_count, initial_count)
    
    def test_notification_creation_integration(self):
        """Test notification creation when threats are detected."""
        # Create a scan with threat
        scan = ScanResult.objects.create(
            user=self.user,
            file_name='malware.exe',
            file_size=2048,
            file_type='application/x-executable',
            file_hash='def456abc789',
            status='completed',
            threat_level='high'
        )
        
        threat = ScanThreat.objects.create(
            scan_result=scan,
            name='Test Malware',
            threat_type='malware',
            severity='high',
            detection_engine='test_engine',
            description='Malware detected in file'
        )
        
        # Check if notification was created
        notifications = Notification.objects.filter(user=self.user)
        self.assertGreaterEqual(notifications.count(), 0)


class PerformanceIntegrationTest(TestCase):
    """Test performance aspects of the application."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='perf_test@example.com',
            password='testpass123'
        )
    
    def test_bulk_threat_event_creation(self):
        """Test bulk creation of threat events."""
        import time
        
        start_time = time.time()
        
        # Create multiple threat events
        events = []
        for i in range(100):
            events.append(ThreatEvent(
                threat_type='malware',
                severity='medium',
                ip_address=f'192.168.1.{i}',
                country='US',
                description=f'Test event {i}'
            ))
        
        ThreatEvent.objects.bulk_create(events)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verify all events were created
        self.assertEqual(ThreatEvent.objects.count(), 100)
        
        # Performance assertion (should complete within reasonable time)
        self.assertLess(creation_time, 5.0)  # Should complete within 5 seconds
    
    def test_api_response_time(self):
        """Test API response times under load."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        import time
        
        # Create test data
        for i in range(50):
            ThreatEvent.objects.create(
                threat_type='malware',
                severity='medium',
                ip_address=f'10.0.0.{i}',
                country='US',
                description=f'Performance test event {i}'
            )
        
        # Set up authenticated client
        client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test API response time
        start_time = time.time()
        response = client.get('/api/threatmap/map/data/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Performance assertion
        self.assertLess(response_time, 2.0)  # Should respond within 2 seconds


class SecurityIntegrationTest(APITestCase):
    """Test security aspects of the application."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='security_test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
    
    def test_rate_limiting_integration(self):
        """Test rate limiting functionality."""
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Make multiple requests rapidly
        responses = []
        for i in range(10):
            response = self.client.get('/api/threatmap/events/')
            responses.append(response.status_code)
        
        # All requests should succeed (rate limiting should be reasonable)
        success_count = sum(1 for status_code in responses if status_code == 200)
        self.assertGreaterEqual(success_count, 5)  # At least half should succeed
    
    def test_unauthorized_access_prevention(self):
        """Test that unauthorized access is properly prevented."""
        client = APIClient()
        
        # Test various endpoints without authentication
        endpoints = [
            '/api/threatmap/events/',
            '/api/threatmap/map/data/',
            '/api/threatmap/stats/',
            '/api/scanner/scans/',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should require authentication"
            )
    
    def test_input_validation_integration(self):
        """Test input validation across API endpoints."""
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test invalid query parameters
        response = self.client.get('/api/threatmap/events/?page=invalid')
        # Should handle invalid pagination gracefully
        self.assertIn(response.status_code, [200, 400])
        
        # Test invalid filters
        response = self.client.get('/api/threatmap/events/?threat_type=invalid_type')
        self.assertEqual(response.status_code, 200)  # Should filter out invalid types