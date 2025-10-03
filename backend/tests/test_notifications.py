from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from notifications.models import Notification
from scanner.models import ScanResult, ScanThreat
from threatmap.models import ThreatEvent, GlobalThreatStats

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test creating a notification instance."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='scan_complete',
            title='Scan Complete',
            message='Your file scan has completed successfully.',
            is_read=False
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'scan_complete')
        self.assertEqual(notification.title, 'Scan Complete')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
    
    def test_notification_str_representation(self):
        """Test string representation of notification."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='threat_detected',
            title='Threat Detected',
            message='A threat was detected in your uploaded file.'
        )
        
        expected_str = f"{self.user.email} - Threat Detected"
        self.assertEqual(str(notification), expected_str)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='security_alert',
            title='Security Alert',
            message='Security alert message.'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_type_choices(self):
        """Test notification type choices."""
        valid_types = [
            'scan_complete', 'threat_detected', 'security_alert',
            'system_notification', 'email_sent'
        ]
        
        for notification_type in valid_types:
            notification = Notification.objects.create(
                user=self.user,
                title=f'Test {notification_type}',
                message=f'Test {notification_type} message',
                notification_type=notification_type,
                priority='medium'
            )
            self.assertEqual(notification.notification_type, notification_type)
    
    def test_notification_priority_choices(self):
        """Test notification priority choices."""
        valid_priorities = ['low', 'medium', 'high', 'critical']
        
        for priority in valid_priorities:
            notification = Notification.objects.create(
                user=self.user,
                title=f'Test {priority} priority',
                message=f'Test {priority} priority message',
                notification_type='security_alert',
                priority=priority
            )
            self.assertEqual(notification.priority, priority)
    
    def test_notification_default_values(self):
        """Test default values for notification."""
        notification = Notification.objects.create(
            user=self.user,
            title='Minimal Notification',
            message='Minimal message',
            notification_type='system_notification'
        )
        
        self.assertEqual(notification.priority, 'medium')  # Default priority
        self.assertFalse(notification.is_read)  # Default is_read
        self.assertEqual(notification.metadata, {})  # Default metadata
    
    def test_notification_ordering(self):
        """Test notification ordering by created_at."""
        notification1 = Notification.objects.create(
            user=self.user,
            title='First Notification',
            message='First message',
            notification_type='system_notification',
            priority='medium'
        )
        
        notification2 = Notification.objects.create(
            user=self.user,
            title='Second Notification',
            message='Second message',
            notification_type='system_notification',
            priority='high'
        )
        
        notifications = Notification.objects.all()
        
        # Should be ordered by created_at descending
        self.assertEqual(notifications.first(), notification2)
        self.assertEqual(notifications.last(), notification1)
    
    def test_notification_metadata(self):
        """Test notification metadata field."""
        metadata = {
            'scan_id': 'test-scan-123',
            'threat_count': 2,
            'file_name': 'test.exe'
        }
        
        notification = Notification.objects.create(
            user=self.user,
            title='Scan Complete',
            message='Scan completed with threats',
            notification_type='scan_complete',
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata['scan_id'], 'test-scan-123')
        self.assertEqual(notification.metadata['threat_count'], 2)
        self.assertEqual(notification.metadata['file_name'], 'test.exe')


class NotificationIntegrationTest(TestCase):
    """Test cases for notification integration with other models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test scan result
        self.scan_result = ScanResult.objects.create(
            user=self.user,
            file_name='test.exe',
            file_size=1024,
            file_hash='abc123def456',
            scan_status='completed',
            threat_level='high'
        )
        
        # Create test threat
        self.scan_threat = ScanThreat.objects.create(
            scan_result=self.scan_result,
            name='Test.Virus',
            threat_type='virus',
            description='Test virus description',
            detection_engine='clamav',
            severity='high'
        )
    
    def test_notification_with_scan_reference(self):
        """Test creating notification with scan result reference."""
        notification = Notification.objects.create(
            user=self.user,
            title='Scan Complete',
            message='Your file scan has completed',
            notification_type='scan_complete',
            scan_result_id=self.scan_result.id,
            metadata={
                'scan_id': str(self.scan_result.id),
                'file_name': self.scan_result.file_name,
                'threats_found': 1
            }
        )
        
        self.assertEqual(notification.scan_result_id, self.scan_result.id)
        self.assertEqual(notification.metadata['file_name'], 'test.exe')
        self.assertEqual(notification.metadata['threats_found'], 1)
    
    def test_notification_with_threat_reference(self):
        """Test creating notification with threat reference."""
        notification = Notification.objects.create(
            user=self.user,
            title='Threat Detected',
            message='A threat was detected in your file',
            notification_type='threat_detected',
            threat_id=self.scan_threat.id,
            priority='high',
            metadata={
                'threat_name': self.scan_threat.name,
                'threat_type': self.scan_threat.threat_type,
                'severity': self.scan_threat.severity
            }
        )
        
        self.assertEqual(notification.threat_id, self.scan_threat.id)
        self.assertEqual(notification.metadata['threat_name'], 'Test.Virus')
        self.assertEqual(notification.priority, 'high')


class NotificationAPITest(APITestCase):
    """Test cases for Notification API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            title='Test Notification 1',
            message='Test message 1',
            notification_type='security_alert',
            priority='high'
        )
        
        self.notification2 = Notification.objects.create(
            user=self.user,
            title='Test Notification 2',
            message='Test message 2',
            notification_type='scan_complete',
            priority='medium',
            is_read=True
        )
    
    def test_notification_list(self):
        """Test retrieving notification list."""
        response = self.client.get('/api/users/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_notification_list_filter_unread(self):
        """Test filtering notifications by read status."""
        response = self.client.get('/api/users/notifications/?is_read=false')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Notification 1')
    
    def test_notification_list_filter_by_type(self):
        """Test filtering notifications by type."""
        response = self.client.get('/api/users/notifications/?notification_type=security_alert')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['notification_type'], 'security_alert')
    
    def test_notification_detail(self):
        """Test retrieving notification details."""
        response = self.client.get(f'/api/users/notifications/{self.notification1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Notification 1')
        self.assertEqual(response.data['priority'], 'high')
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        response = self.client.patch(
            f'/api/users/notifications/{self.notification1.id}/',
            {'is_read': True}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        
        # Verify in database
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
    
    def test_notification_delete(self):
        """Test deleting a notification."""
        response = self.client.delete(f'/api/users/notifications/{self.notification1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify notification was deleted
        self.assertFalse(
            Notification.objects.filter(id=self.notification1.id).exists()
        )
    
    def test_unauthorized_access(self):
        """Test unauthorized access to notifications."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/users/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_isolation(self):
        """Test that users can only see their own notifications."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        # Create notification for other user
        Notification.objects.create(
            user=other_user,
            title='Other User Notification',
            message='Other user message',
            notification_type='system_notification'
        )
        
        response = self.client.get('/api/users/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only current user's notifications
        
        # Verify notification titles
        titles = [notif['title'] for notif in response.data]
        self.assertIn('Test Notification 1', titles)
        self.assertIn('Test Notification 2', titles)
        self.assertNotIn('Other User Notification', titles)