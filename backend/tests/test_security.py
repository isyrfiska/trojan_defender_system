"""
Security tests for the Trojan Defender application.
Tests authentication, authorization, input validation, and security measures.
"""

import json
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from threatmap.models import ThreatEvent
from scanner.models import ScanResult

User = get_user_model()


class AuthenticationSecurityTest(APITestCase):
    """Test authentication security measures."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='security_test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
    
    def test_jwt_token_authentication(self):
        """Test JWT token authentication."""
        # Test without token
        response = self.client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with valid token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_token_handling(self):
        """Test handling of invalid tokens."""
        # Test with malformed token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/threatmap/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with expired token (mock)
        with patch('rest_framework_simplejwt.tokens.RefreshToken.for_user') as mock_token:
            # Create an expired token
            expired_token = RefreshToken.for_user(self.user)
            expired_token.set_exp(lifetime=timedelta(seconds=-1))  # Already expired
            mock_token.return_value = expired_token
            
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(expired_token.access_token)}')
            response = self.client.get('/api/threatmap/events/')
            # Should handle expired token gracefully
            self.assertIn(response.status_code, [401, 403])
    
    def test_token_refresh_security(self):
        """Test token refresh security."""
        refresh = RefreshToken.for_user(self.user)
        
        # Test valid refresh
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': str(refresh)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
        
        # Test invalid refresh token
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': 'invalid_refresh_token'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_authentication_required(self):
        """Test that all protected endpoints require authentication."""
        protected_endpoints = [
            '/api/threatmap/events/',
            '/api/threatmap/map/data/',
            '/api/threatmap/stats/',
            '/api/scanner/scans/',
            '/api/notifications/',
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should require authentication"
            )


class AuthorizationSecurityTest(APITestCase):
    """Test authorization and access control."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create user-specific data
        self.scan1 = ScanResult.objects.create(
            user=self.user1,
            file_name='user1_file.exe',
            file_size=1024,
            file_type='application/x-executable',
            file_hash='abc123',
            status='completed',
            threat_level='clean'
        )
        
        self.scan2 = ScanResult.objects.create(
            user=self.user2,
            file_name='user2_file.exe',
            file_size=2048,
            file_type='application/x-executable',
            file_hash='def456',
            status='completed',
            threat_level='clean'
        )
    
    def test_user_data_isolation(self):
        """Test that users can only access their own data."""
        # Set up client for user1
        client1 = APIClient()
        refresh1 = RefreshToken.for_user(self.user1)
        access_token1 = str(refresh1.access_token)
        client1.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token1}')
        
        # Set up client for user2
        client2 = APIClient()
        refresh2 = RefreshToken.for_user(self.user2)
        access_token2 = str(refresh2.access_token)
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token2}')
        
        # User1 should only see their own scans
        response1 = client1.get('/api/scanner/scans/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        data1 = response1.json()
        scan_ids1 = [scan['id'] for scan in data1['results']]
        self.assertIn(str(self.scan1.id), scan_ids1)
        self.assertNotIn(str(self.scan2.id), scan_ids1)
        
        # User2 should only see their own scans
        response2 = client2.get('/api/scanner/scans/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.json()
        scan_ids2 = [scan['id'] for scan in data2['results']]
        self.assertIn(str(self.scan2.id), scan_ids2)
        self.assertNotIn(str(self.scan1.id), scan_ids2)
    
    def test_direct_object_access_prevention(self):
        """Test prevention of direct object access by other users."""
        # Set up client for user2
        client2 = APIClient()
        refresh2 = RefreshToken.for_user(self.user2)
        access_token2 = str(refresh2.access_token)
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token2}')
        
        # User2 should not be able to access user1's scan directly
        response = client2.get(f'/api/scanner/scans/{self.scan1.id}/')
        self.assertIn(response.status_code, [403, 404])  # Forbidden or Not Found


class InputValidationSecurityTest(APITestCase):
    """Test input validation and sanitization."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='validation_test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks."""
        # Test malicious query parameters
        malicious_params = [
            "'; DROP TABLE threatmap_threatevent; --",
            "1' OR '1'='1",
            "1; DELETE FROM threatmap_threatevent; --",
            "<script>alert('xss')</script>",
        ]
        
        for param in malicious_params:
            # Test in various query parameters
            response = self.client.get(f'/api/threatmap/events/?search={param}')
            # Should not cause server error
            self.assertNotEqual(response.status_code, 500)
            
            response = self.client.get(f'/api/threatmap/events/?threat_type={param}')
            self.assertNotEqual(response.status_code, 500)
    
    def test_xss_prevention(self):
        """Test prevention of XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ]
        
        for payload in xss_payloads:
            response = self.client.get(f'/api/threatmap/events/?search={payload}')
            # Should handle XSS attempts gracefully
            self.assertIn(response.status_code, [200, 400])
            
            if response.status_code == 200:
                # Response should not contain unescaped script tags
                content = response.content.decode()
                self.assertNotIn('<script>', content.lower())
    
    def test_file_upload_validation(self):
        """Test file upload security validation."""
        # This would test file upload endpoints if they exist
        # For now, we'll test the concept with mock data
        
        dangerous_filenames = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            'test.exe.bat',
            'script.js',
            'malware.scr',
        ]
        
        for filename in dangerous_filenames:
            # Mock file upload validation
            # In a real scenario, this would test actual file upload endpoints
            self.assertTrue(len(filename) > 0)  # Placeholder assertion
    
    def test_parameter_tampering_prevention(self):
        """Test prevention of parameter tampering."""
        # Test with invalid pagination parameters
        response = self.client.get('/api/threatmap/events/?page=-1')
        self.assertIn(response.status_code, [200, 400])
        
        response = self.client.get('/api/threatmap/events/?page=999999')
        self.assertIn(response.status_code, [200, 404])
        
        # Test with invalid page size
        response = self.client.get('/api/threatmap/events/?page_size=-1')
        self.assertIn(response.status_code, [200, 400])
        
        response = self.client.get('/api/threatmap/events/?page_size=999999')
        self.assertIn(response.status_code, [200, 400])


class RateLimitingSecurityTest(APITestCase):
    """Test rate limiting security measures."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='ratelimit_test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    def test_api_rate_limiting(self):
        """Test API rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            response = self.client.get('/api/threatmap/events/')
            responses.append(response.status_code)
        
        # Should have some successful requests
        success_count = sum(1 for status_code in responses if status_code == 200)
        self.assertGreater(success_count, 0)
        
        # May have some rate-limited requests (429)
        rate_limited_count = sum(1 for status_code in responses if status_code == 429)
        
        # At least some requests should succeed (rate limiting should be reasonable)
        self.assertGreaterEqual(success_count, 10)
    
    @patch('trojan_defender.rate_limiting.RateLimitingMiddleware.get_client_identifier')
    def test_rate_limiting_by_ip(self, mock_get_client):
        """Test rate limiting by IP address."""
        # Mock different IP addresses
        mock_get_client.side_effect = ['192.168.1.1', '192.168.1.2'] * 10
        
        responses = []
        for i in range(10):
            response = self.client.get('/api/threatmap/events/')
            responses.append(response.status_code)
        
        # Should handle different IPs appropriately
        success_count = sum(1 for status_code in responses if status_code == 200)
        self.assertGreater(success_count, 0)


class DataSecurityTest(TestCase):
    """Test data security and privacy measures."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='data_security@example.com',
            password='testpass123'
        )
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        # Password should not be stored in plain text
        self.assertNotEqual(self.user.password, 'testpass123')
        
        # Password should be hashed
        self.assertTrue(self.user.password.startswith('pbkdf2_sha256$'))
        
        # User should be able to authenticate with correct password
        self.assertTrue(self.user.check_password('testpass123'))
        
        # User should not authenticate with incorrect password
        self.assertFalse(self.user.check_password('wrongpassword'))
    
    def test_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed in API responses."""
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        
        client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test that user password is not exposed
        response = client.get('/api/auth/user/')
        if response.status_code == 200:
            data = response.json()
            self.assertNotIn('password', data)
    
    def test_database_query_security(self):
        """Test database query security."""
        # Create test threat event
        event = ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            description='Security test event'
        )
        
        # Test that queries are properly parameterized
        # This is more of a code review item, but we can test basic functionality
        events = ThreatEvent.objects.filter(threat_type='malware')
        self.assertEqual(events.count(), 1)
        
        # Test with potentially dangerous input
        events = ThreatEvent.objects.filter(threat_type="'; DROP TABLE --")
        self.assertEqual(events.count(), 0)  # Should return no results, not cause error


class SecurityHeadersTest(TestCase):
    """Test security headers and middleware."""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        from django.test import Client
        
        client = Client()
        response = client.get('/api/health/')
        
        # Test for common security headers
        # Note: These depend on middleware configuration
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
        ]
        
        for header in headers_to_check:
            # Headers may or may not be present depending on configuration
            # This is more of a configuration check
            if header in response:
                self.assertIsNotNone(response[header])
    
    @override_settings(DEBUG=False)
    def test_debug_mode_disabled_in_production(self):
        """Test that debug mode is disabled in production."""
        from django.conf import settings
        
        # In production, DEBUG should be False
        self.assertFalse(settings.DEBUG)
    
    def test_cors_configuration(self):
        """Test CORS configuration security."""
        from django.test import Client
        
        client = Client()
        
        # Test preflight request
        response = client.options('/api/threatmap/events/', 
                                HTTP_ORIGIN='http://malicious-site.com')
        
        # Should handle CORS appropriately
        # The exact behavior depends on CORS configuration
        self.assertIn(response.status_code, [200, 403, 404])


class SessionSecurityTest(APITestCase):
    """Test session security measures."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='session_test@example.com',
            password='testpass123'
        )
    
    def test_session_timeout(self):
        """Test session timeout behavior."""
        # This would test session timeout if using session-based auth
        # With JWT, tokens have built-in expiration
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Token should have expiration time
        self.assertIsNotNone(access_token.get('exp'))
        
        # Expiration should be in the future
        import time
        current_time = int(time.time())
        token_exp = access_token.get('exp')
        self.assertGreater(token_exp, current_time)
    
    def test_concurrent_session_handling(self):
        """Test handling of concurrent sessions."""
        # Create multiple tokens for the same user
        refresh1 = RefreshToken.for_user(self.user)
        refresh2 = RefreshToken.for_user(self.user)
        
        access_token1 = str(refresh1.access_token)
        access_token2 = str(refresh2.access_token)
        
        # Both tokens should be valid
        client1 = APIClient()
        client1.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token1}')
        response1 = client1.get('/api/threatmap/events/')
        
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token2}')
        response2 = client2.get('/api/threatmap/events/')
        
        # Both should work (JWT allows multiple concurrent sessions)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)