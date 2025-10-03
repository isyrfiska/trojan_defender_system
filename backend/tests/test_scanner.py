import os
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from scanner.models import Scan, Threat
from scanner.services import ScannerService

User = get_user_model()


class ScanModelTest(TestCase):
    """Test cases for Scan model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_scan_creation(self):
        """Test creating a scan instance."""
        scan = Scan.objects.create(
            user=self.user,
            filename='test.exe',
            file_size=1024,
            file_hash='abc123',
            status='pending'
        )
        
        self.assertEqual(scan.user, self.user)
        self.assertEqual(scan.filename, 'test.exe')
        self.assertEqual(scan.file_size, 1024)
        self.assertEqual(scan.file_hash, 'abc123')
        self.assertEqual(scan.status, 'pending')
        self.assertIsNotNone(scan.created_at)
    
    def test_scan_str_representation(self):
        """Test string representation of scan."""
        scan = Scan.objects.create(
            user=self.user,
            filename='test.exe',
            file_size=1024,
            file_hash='abc123',
            status='pending'
        )
        
        expected_str = f"Scan {scan.id}: test.exe (pending)"
        self.assertEqual(str(scan), expected_str)
    
    def test_scan_status_choices(self):
        """Test scan status choices."""
        valid_statuses = ['pending', 'scanning', 'completed', 'failed']
        
        for status in valid_statuses:
            scan = Scan.objects.create(
                user=self.user,
                filename=f'test_{status}.exe',
                file_size=1024,
                file_hash=f'hash_{status}',
                status=status
            )
            self.assertEqual(scan.status, status)


class ThreatModelTest(TestCase):
    """Test cases for Threat model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.scan = Scan.objects.create(
            user=self.user,
            filename='malware.exe',
            file_size=2048,
            file_hash='def456',
            status='completed'
        )
    
    def test_threat_creation(self):
        """Test creating a threat instance."""
        threat = Threat.objects.create(
            scan=self.scan,
            threat_name='Trojan.Win32.Test',
            threat_type='trojan',
            severity='high',
            description='Test trojan description',
            engine='clamav'
        )
        
        self.assertEqual(threat.scan, self.scan)
        self.assertEqual(threat.threat_name, 'Trojan.Win32.Test')
        self.assertEqual(threat.threat_type, 'trojan')
        self.assertEqual(threat.severity, 'high')
        self.assertEqual(threat.description, 'Test trojan description')
        self.assertEqual(threat.engine, 'clamav')
    
    def test_threat_str_representation(self):
        """Test string representation of threat."""
        threat = Threat.objects.create(
            scan=self.scan,
            threat_name='Trojan.Win32.Test',
            threat_type='trojan',
            severity='high',
            description='Test trojan description',
            engine='clamav'
        )
        
        expected_str = "Trojan.Win32.Test (high)"
        self.assertEqual(str(threat), expected_str)
    
    def test_threat_severity_choices(self):
        """Test threat severity choices."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        
        for severity in valid_severities:
            threat = Threat.objects.create(
                scan=self.scan,
                threat_name=f'Test.{severity}',
                threat_type='virus',
                severity=severity,
                description=f'Test {severity} threat',
                engine='clamav'
            )
            self.assertEqual(threat.severity, severity)


class ScannerServiceTest(TestCase):
    """Test cases for ScannerService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.service = ScannerService()
    
    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'test content')
            temp_file_path = temp_file.name
        
        try:
            file_hash = self.service.calculate_file_hash(temp_file_path)
            
            # Expected SHA-256 hash of 'test content'
            expected_hash = '1eebdf4fdc9fc7bf283031b93f9aef3338de9052f584b10f4e8c59d6b3c9b8b8'
            self.assertEqual(file_hash, expected_hash)
        finally:
            os.unlink(temp_file_path)
    
    @patch('scanner.services.subprocess.run')
    def test_scan_with_clamav_clean(self, mock_subprocess):
        """Test ClamAV scanning with clean file."""
        # Mock ClamAV returning clean result
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout='test.txt: OK\n'
        )
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'clean content')
            temp_file_path = temp_file.name
        
        try:
            result = self.service.scan_with_clamav(temp_file_path)
            
            self.assertTrue(result['is_clean'])
            self.assertEqual(result['threats'], [])
            self.assertIn('OK', result['output'])
        finally:
            os.unlink(temp_file_path)
    
    @patch('scanner.services.subprocess.run')
    def test_scan_with_clamav_infected(self, mock_subprocess):
        """Test ClamAV scanning with infected file."""
        # Mock ClamAV returning infected result
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout='test.txt: Eicar-Test-Signature FOUND\n'
        )
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'infected content')
            temp_file_path = temp_file.name
        
        try:
            result = self.service.scan_with_clamav(temp_file_path)
            
            self.assertFalse(result['is_clean'])
            self.assertEqual(len(result['threats']), 1)
            self.assertEqual(result['threats'][0], 'Eicar-Test-Signature')
        finally:
            os.unlink(temp_file_path)
    
    @patch('scanner.services.yara')
    def test_scan_with_yara_clean(self, mock_yara):
        """Test YARA scanning with clean file."""
        # Mock YARA rules and clean result
        mock_rules = MagicMock()
        mock_rules.match.return_value = []
        mock_yara.compile.return_value = mock_rules
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'clean content')
            temp_file_path = temp_file.name
        
        try:
            result = self.service.scan_with_yara(temp_file_path)
            
            self.assertTrue(result['is_clean'])
            self.assertEqual(result['threats'], [])
        finally:
            os.unlink(temp_file_path)
    
    @patch('scanner.services.yara')
    def test_scan_with_yara_infected(self, mock_yara):
        """Test YARA scanning with infected file."""
        # Mock YARA rules and infected result
        mock_match = MagicMock()
        mock_match.rule = 'TestMalware'
        mock_rules = MagicMock()
        mock_rules.match.return_value = [mock_match]
        mock_yara.compile.return_value = mock_rules
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'infected content')
            temp_file_path = temp_file.name
        
        try:
            result = self.service.scan_with_yara(temp_file_path)
            
            self.assertFalse(result['is_clean'])
            self.assertEqual(len(result['threats']), 1)
            self.assertEqual(result['threats'][0], 'TestMalware')
        finally:
            os.unlink(temp_file_path)


class ScanAPITest(APITestCase):
    """Test cases for Scan API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_scan_list_authenticated(self):
        """Test listing scans for authenticated user."""
        # Create test scans
        Scan.objects.create(
            user=self.user,
            filename='test1.exe',
            file_size=1024,
            file_hash='hash1',
            status='completed'
        )
        Scan.objects.create(
            user=self.user,
            filename='test2.exe',
            file_size=2048,
            file_hash='hash2',
            status='pending'
        )
        
        response = self.client.get('/api/scanner/scans/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_scan_list_unauthenticated(self):
        """Test listing scans without authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/scanner/scans/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_scan_detail_authenticated(self):
        """Test retrieving scan details for authenticated user."""
        scan = Scan.objects.create(
            user=self.user,
            filename='test.exe',
            file_size=1024,
            file_hash='hash123',
            status='completed'
        )
        
        response = self.client.get(f'/api/scanner/scans/{scan.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filename'], 'test.exe')
        self.assertEqual(response.data['status'], 'completed')
    
    def test_scan_detail_other_user(self):
        """Test retrieving scan details for different user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        scan = Scan.objects.create(
            user=other_user,
            filename='test.exe',
            file_size=1024,
            file_hash='hash123',
            status='completed'
        )
        
        response = self.client.get(f'/api/scanner/scans/{scan.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('scanner.tasks.scan_file.delay')
    def test_file_upload_valid(self, mock_scan_task):
        """Test uploading a valid file for scanning."""
        # Mock Celery task
        mock_scan_task.return_value = MagicMock(id='task-123')
        
        # Create test file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"file content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            '/api/scanner/upload/',
            {'file': test_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('scan_id', response.data)
        self.assertIn('task_id', response.data)
        
        # Verify scan was created
        scan = Scan.objects.get(id=response.data['scan_id'])
        self.assertEqual(scan.filename, 'test.txt')
        self.assertEqual(scan.user, self.user)
        self.assertEqual(scan.status, 'pending')
    
    def test_file_upload_no_file(self):
        """Test uploading without providing a file."""
        response = self.client.post(
            '/api/scanner/upload/',
            {},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
    
    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=100)
    def test_file_upload_too_large(self):
        """Test uploading a file that's too large."""
        # Create large test file
        large_content = b"x" * 200  # Larger than the 100 byte limit
        test_file = SimpleUploadedFile(
            "large.txt",
            large_content,
            content_type="text/plain"
        )
        
        response = self.client.post(
            '/api/scanner/upload/',
            {'file': test_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_scan_statistics(self):
        """Test retrieving scan statistics."""
        # Create test scans with different statuses
        Scan.objects.create(
            user=self.user,
            filename='clean1.txt',
            file_size=1024,
            file_hash='hash1',
            status='completed'
        )
        Scan.objects.create(
            user=self.user,
            filename='clean2.txt',
            file_size=1024,
            file_hash='hash2',
            status='completed'
        )
        
        # Create scan with threat
        infected_scan = Scan.objects.create(
            user=self.user,
            filename='infected.exe',
            file_size=2048,
            file_hash='hash3',
            status='completed'
        )
        Threat.objects.create(
            scan=infected_scan,
            threat_name='TestVirus',
            threat_type='virus',
            severity='high',
            description='Test virus',
            engine='clamav'
        )
        
        response = self.client.get('/api/scanner/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_scans'], 3)
        self.assertEqual(response.data['clean_files'], 2)
        self.assertEqual(response.data['threats_found'], 1)
        self.assertIn('scan_history', response.data)


class ThreatAPITest(APITestCase):
    """Test cases for Threat API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test scan and threats
        self.scan = Scan.objects.create(
            user=self.user,
            filename='malware.exe',
            file_size=2048,
            file_hash='hash123',
            status='completed'
        )
        
        self.threat1 = Threat.objects.create(
            scan=self.scan,
            threat_name='Trojan.Win32.Test',
            threat_type='trojan',
            severity='high',
            description='Test trojan',
            engine='clamav'
        )
        
        self.threat2 = Threat.objects.create(
            scan=self.scan,
            threat_name='Virus.Win32.Test',
            threat_type='virus',
            severity='medium',
            description='Test virus',
            engine='yara'
        )
    
    def test_threat_list_authenticated(self):
        """Test listing threats for authenticated user."""
        response = self.client.get('/api/scanner/threats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_threat_list_filtered_by_severity(self):
        """Test listing threats filtered by severity."""
        response = self.client.get('/api/scanner/threats/?severity=high')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['severity'], 'high')
    
    def test_threat_list_filtered_by_type(self):
        """Test listing threats filtered by type."""
        response = self.client.get('/api/scanner/threats/?threat_type=trojan')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['threat_type'], 'trojan')
    
    def test_threat_detail_authenticated(self):
        """Test retrieving threat details for authenticated user."""
        response = self.client.get(f'/api/scanner/threats/{self.threat1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['threat_name'], 'Trojan.Win32.Test')
        self.assertEqual(response.data['severity'], 'high')
    
    def test_threat_statistics(self):
        """Test retrieving threat statistics."""
        response = self.client.get('/api/scanner/threat-statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_threats', response.data)
        self.assertIn('by_severity', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('by_engine', response.data)
        
        # Check specific counts
        self.assertEqual(response.data['total_threats'], 2)
        self.assertEqual(response.data['by_severity']['high'], 1)
        self.assertEqual(response.data['by_severity']['medium'], 1)
        self.assertEqual(response.data['by_type']['trojan'], 1)
        self.assertEqual(response.data['by_type']['virus'], 1)