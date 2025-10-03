from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os

from reports.models import Report, ReportTemplate
from reports.services import ReportService
from scanner.models import Scan, Threat
from threat_map.models import ThreatData, ThreatSource

User = get_user_model()


class ReportTemplateModelTest(TestCase):
    """Test cases for ReportTemplate model."""
    
    def test_report_template_creation(self):
        """Test creating a report template instance."""
        template = ReportTemplate.objects.create(
            name='Security Summary',
            description='Weekly security summary report',
            template_type='security_summary',
            template_content={
                'sections': ['overview', 'threats', 'recommendations'],
                'format': 'pdf'
            },
            is_active=True
        )
        
        self.assertEqual(template.name, 'Security Summary')
        self.assertEqual(template.description, 'Weekly security summary report')
        self.assertEqual(template.template_type, 'security_summary')
        self.assertIn('sections', template.template_content)
        self.assertTrue(template.is_active)
        self.assertIsNotNone(template.created_at)
    
    def test_report_template_str_representation(self):
        """Test string representation of report template."""
        template = ReportTemplate.objects.create(
            name='Test Template',
            description='Test description',
            template_type='custom',
            template_content={},
            is_active=True
        )
        
        self.assertEqual(str(template), 'Test Template')
    
    def test_report_template_type_choices(self):
        """Test report template type choices."""
        valid_types = [
            'security_summary', 'threat_analysis', 'scan_report',
            'compliance', 'incident_response', 'custom'
        ]
        
        for template_type in valid_types:
            template = ReportTemplate.objects.create(
                name=f'Test {template_type}',
                description=f'Test {template_type} template',
                template_type=template_type,
                template_content={},
                is_active=True
            )
            self.assertEqual(template.template_type, template_type)
    
    def test_report_template_default_values(self):
        """Test default values for report template."""
        template = ReportTemplate.objects.create(
            name='Minimal Template',
            template_type='custom',
            template_content={}
        )
        
        self.assertTrue(template.is_active)  # Default should be True
        self.assertEqual(template.template_content, {})


class ReportModelTest(TestCase):
    """Test cases for Report model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.template = ReportTemplate.objects.create(
            name='Test Template',
            description='Test template',
            template_type='security_summary',
            template_content={'format': 'pdf'},
            is_active=True
        )
    
    def test_report_creation(self):
        """Test creating a report instance."""
        report = Report.objects.create(
            user=self.user,
            template=self.template,
            title='Weekly Security Report',
            report_type='security_summary',
            status='completed',
            file_path='/reports/weekly_report.pdf',
            parameters={
                'date_range': '7_days',
                'include_charts': True
            }
        )
        
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.template, self.template)
        self.assertEqual(report.title, 'Weekly Security Report')
        self.assertEqual(report.report_type, 'security_summary')
        self.assertEqual(report.status, 'completed')
        self.assertEqual(report.file_path, '/reports/weekly_report.pdf')
        self.assertIn('date_range', report.parameters)
        self.assertIsNotNone(report.created_at)
    
    def test_report_str_representation(self):
        """Test string representation of report."""
        report = Report.objects.create(
            user=self.user,
            template=self.template,
            title='Test Report',
            report_type='custom',
            status='pending'
        )
        
        expected_str = f"Report {report.id}: Test Report (pending)"
        self.assertEqual(str(report), expected_str)
    
    def test_report_status_choices(self):
        """Test report status choices."""
        valid_statuses = ['pending', 'generating', 'completed', 'failed']
        
        for status in valid_statuses:
            report = Report.objects.create(
                user=self.user,
                template=self.template,
                title=f'Test {status} Report',
                report_type='custom',
                status=status
            )
            self.assertEqual(report.status, status)
    
    def test_report_type_choices(self):
        """Test report type choices."""
        valid_types = [
            'security_summary', 'threat_analysis', 'scan_report',
            'compliance', 'incident_response', 'custom'
        ]
        
        for report_type in valid_types:
            report = Report.objects.create(
                user=self.user,
                template=self.template,
                title=f'Test {report_type} Report',
                report_type=report_type,
                status='pending'
            )
            self.assertEqual(report.report_type, report_type)
    
    def test_report_ordering(self):
        """Test report ordering by created_at."""
        report1 = Report.objects.create(
            user=self.user,
            template=self.template,
            title='First Report',
            report_type='custom',
            status='completed'
        )
        
        report2 = Report.objects.create(
            user=self.user,
            template=self.template,
            title='Second Report',
            report_type='custom',
            status='pending'
        )
        
        reports = Report.objects.all()
        
        # Should be ordered by created_at descending
        self.assertEqual(reports.first(), report2)
        self.assertEqual(reports.last(), report1)


class ReportServiceTest(TestCase):
    """Test cases for ReportService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.service = ReportService()
        
        # Create test data
        self.template = ReportTemplate.objects.create(
            name='Security Summary Template',
            description='Security summary template',
            template_type='security_summary',
            template_content={
                'sections': ['overview', 'threats', 'scans'],
                'format': 'pdf'
            },
            is_active=True
        )
        
        # Create test scan data
        self.scan = Scan.objects.create(
            user=self.user,
            filename='test.exe',
            file_size=1024,
            file_hash='abc123',
            status='completed'
        )
        
        self.threat = Threat.objects.create(
            scan=self.scan,
            threat_name='Test.Virus',
            threat_type='virus',
            severity='high',
            description='Test virus',
            engine='clamav'
        )
        
        # Create test threat map data
        self.threat_source = ThreatSource.objects.create(
            name='Test Source',
            url='https://example.com',
            source_type='api',
            is_active=True
        )
        
        self.threat_data = ThreatData.objects.create(
            source=self.threat_source,
            threat_type='malware',
            severity='high',
            latitude=40.7128,
            longitude=-74.0060,
            country='US',
            city='New York',
            description='Malware detected'
        )
    
    def test_collect_scan_data(self):
        """Test collecting scan data for reports."""
        data = self.service.collect_scan_data(self.user)
        
        self.assertIn('total_scans', data)
        self.assertIn('completed_scans', data)
        self.assertIn('threats_found', data)
        self.assertIn('clean_files', data)
        self.assertIn('recent_scans', data)
        self.assertIn('threat_breakdown', data)
        
        self.assertEqual(data['total_scans'], 1)
        self.assertEqual(data['completed_scans'], 1)
        self.assertEqual(data['threats_found'], 1)
        self.assertEqual(data['clean_files'], 0)
    
    def test_collect_scan_data_date_range(self):
        """Test collecting scan data with date range."""
        # Create old scan
        old_scan = Scan.objects.create(
            user=self.user,
            filename='old.exe',
            file_size=512,
            file_hash='old123',
            status='completed'
        )
        old_scan.created_at = datetime.now() - timedelta(days=30)
        old_scan.save()
        
        # Get data for last 7 days
        data = self.service.collect_scan_data(self.user, days=7)
        
        # Should only include recent scan
        self.assertEqual(data['total_scans'], 1)
        self.assertEqual(len(data['recent_scans']), 1)
    
    def test_collect_threat_data(self):
        """Test collecting threat data for reports."""
        data = self.service.collect_threat_data()
        
        self.assertIn('total_threats', data)
        self.assertIn('by_type', data)
        self.assertIn('by_severity', data)
        self.assertIn('by_country', data)
        self.assertIn('recent_threats', data)
        
        self.assertEqual(data['total_threats'], 1)
        self.assertEqual(data['by_type']['malware'], 1)
        self.assertEqual(data['by_severity']['high'], 1)
        self.assertEqual(data['by_country']['US'], 1)
    
    def test_collect_threat_data_date_range(self):
        """Test collecting threat data with date range."""
        # Create old threat
        old_threat = ThreatData.objects.create(
            source=self.threat_source,
            threat_type='phishing',
            severity='medium',
            latitude=0.0,
            longitude=0.0,
            country='CA',
            description='Old threat'
        )
        old_threat.timestamp = datetime.now() - timedelta(days=30)
        old_threat.save()
        
        # Get data for last 7 days
        data = self.service.collect_threat_data(days=7)
        
        # Should only include recent threat
        self.assertEqual(data['total_threats'], 1)
        self.assertEqual(len(data['recent_threats']), 1)
    
    def test_generate_security_summary_data(self):
        """Test generating security summary data."""
        data = self.service.generate_security_summary_data(self.user)
        
        self.assertIn('overview', data)
        self.assertIn('scan_data', data)
        self.assertIn('threat_data', data)
        self.assertIn('recommendations', data)
        
        # Check overview section
        overview = data['overview']
        self.assertIn('total_scans', overview)
        self.assertIn('threats_detected', overview)
        self.assertIn('security_score', overview)
    
    def test_generate_threat_analysis_data(self):
        """Test generating threat analysis data."""
        data = self.service.generate_threat_analysis_data()
        
        self.assertIn('threat_overview', data)
        self.assertIn('geographic_distribution', data)
        self.assertIn('threat_trends', data)
        self.assertIn('top_threats', data)
        
        # Check threat overview
        overview = data['threat_overview']
        self.assertIn('total_threats', overview)
        self.assertIn('by_type', overview)
        self.assertIn('by_severity', overview)
    
    def test_generate_scan_report_data(self):
        """Test generating scan report data."""
        data = self.service.generate_scan_report_data(self.user)
        
        self.assertIn('scan_summary', data)
        self.assertIn('detailed_scans', data)
        self.assertIn('threat_details', data)
        self.assertIn('file_analysis', data)
        
        # Check scan summary
        summary = data['scan_summary']
        self.assertIn('total_files_scanned', summary)
        self.assertIn('threats_found', summary)
        self.assertIn('clean_files', summary)
    
    @patch('reports.services.weasyprint.HTML')
    def test_generate_pdf_report_success(self, mock_html):
        """Test successful PDF report generation."""
        # Mock WeasyPrint
        mock_document = MagicMock()
        mock_html.return_value = mock_document
        
        data = {'title': 'Test Report', 'content': 'Test content'}
        template_path = 'reports/security_summary.html'
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = self.service.generate_pdf_report(data, template_path, output_path)
            
            self.assertTrue(result)
            mock_html.assert_called_once()
            mock_document.write_pdf.assert_called_once_with(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('reports.services.weasyprint.HTML')
    def test_generate_pdf_report_failure(self, mock_html):
        """Test PDF report generation failure."""
        # Mock WeasyPrint failure
        mock_html.side_effect = Exception('PDF generation error')
        
        data = {'title': 'Test Report', 'content': 'Test content'}
        template_path = 'reports/security_summary.html'
        output_path = '/tmp/test_report.pdf'
        
        result = self.service.generate_pdf_report(data, template_path, output_path)
        
        self.assertFalse(result)
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        data = {
            'title': 'Test Report',
            'generated_at': datetime.now().isoformat(),
            'data': {'key': 'value'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = self.service.generate_json_report(data, output_path)
            
            self.assertTrue(result)
            
            # Verify file was created and contains correct data
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data['title'], 'Test Report')
            self.assertEqual(saved_data['data']['key'], 'value')
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_create_report_security_summary(self):
        """Test creating a security summary report."""
        parameters = {
            'date_range': 7,
            'format': 'json'
        }
        
        with patch.object(self.service, 'generate_json_report', return_value=True):
            report = self.service.create_report(
                user=self.user,
                template=self.template,
                title='Test Security Summary',
                parameters=parameters
            )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.template, self.template)
        self.assertEqual(report.title, 'Test Security Summary')
        self.assertEqual(report.status, 'completed')
        self.assertIsNotNone(report.file_path)
    
    def test_create_report_failure(self):
        """Test report creation failure."""
        parameters = {
            'date_range': 7,
            'format': 'pdf'
        }
        
        with patch.object(self.service, 'generate_pdf_report', return_value=False):
            report = self.service.create_report(
                user=self.user,
                template=self.template,
                title='Failed Report',
                parameters=parameters
            )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.status, 'failed')
        self.assertIsNone(report.file_path)
    
    def test_get_report_recommendations(self):
        """Test getting security recommendations."""
        scan_data = {
            'threats_found': 5,
            'clean_files': 10,
            'threat_breakdown': {
                'virus': 2,
                'trojan': 2,
                'malware': 1
            }
        }
        
        threat_data = {
            'total_threats': 100,
            'by_severity': {
                'critical': 10,
                'high': 20,
                'medium': 40,
                'low': 30
            }
        }
        
        recommendations = self.service.get_report_recommendations(scan_data, threat_data)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check that recommendations are strings
        for rec in recommendations:
            self.assertIsInstance(rec, str)
    
    def test_calculate_security_score(self):
        """Test calculating security score."""
        scan_data = {
            'total_scans': 20,
            'threats_found': 2,
            'clean_files': 18
        }
        
        threat_data = {
            'total_threats': 50,
            'by_severity': {
                'critical': 5,
                'high': 10,
                'medium': 20,
                'low': 15
            }
        }
        
        score = self.service.calculate_security_score(scan_data, threat_data)
        
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class ReportsAPITest(APITestCase):
    """Test cases for Reports API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.template = ReportTemplate.objects.create(
            name='Test Template',
            description='Test template',
            template_type='security_summary',
            template_content={'format': 'pdf'},
            is_active=True
        )
        
        self.report = Report.objects.create(
            user=self.user,
            template=self.template,
            title='Test Report',
            report_type='security_summary',
            status='completed',
            file_path='/reports/test_report.pdf'
        )
    
    def test_report_list_authenticated(self):
        """Test listing reports for authenticated user."""
        response = self.client.get('/api/reports/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Report')
    
    def test_report_list_unauthenticated(self):
        """Test listing reports without authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/reports/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_report_detail_authenticated(self):
        """Test retrieving report details for authenticated user."""
        response = self.client.get(f'/api/reports/reports/{self.report.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Report')
        self.assertEqual(response.data['status'], 'completed')
    
    def test_report_detail_other_user(self):
        """Test retrieving report details for different user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        other_report = Report.objects.create(
            user=other_user,
            template=self.template,
            title='Other Report',
            report_type='custom',
            status='completed'
        )
        
        response = self.client.get(f'/api/reports/reports/{other_report.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_report_delete(self):
        """Test deleting a report."""
        response = self.client.delete(f'/api/reports/reports/{self.report.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify report was deleted
        self.assertFalse(
            Report.objects.filter(id=self.report.id).exists()
        )
    
    @patch('reports.tasks.generate_report.delay')
    def test_create_report_async(self, mock_task):
        """Test creating a report asynchronously."""
        # Mock Celery task
        mock_task.return_value = MagicMock(id='task-123')
        
        report_data = {
            'template_id': self.template.id,
            'title': 'New Test Report',
            'parameters': {
                'date_range': 7,
                'format': 'pdf'
            }
        }
        
        response = self.client.post(
            '/api/reports/reports/',
            report_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('task_id', response.data)
        
        # Verify report was created
        report = Report.objects.get(id=response.data['id'])
        self.assertEqual(report.title, 'New Test Report')
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.status, 'pending')
    
    def test_create_report_invalid_template(self):
        """Test creating a report with invalid template."""
        report_data = {
            'template_id': 999,  # Non-existent template
            'title': 'Invalid Report',
            'parameters': {}
        }
        
        response = self.client.post(
            '/api/reports/reports/',
            report_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('template_id', response.data)
    
    def test_create_report_missing_title(self):
        """Test creating a report without title."""
        report_data = {
            'template_id': self.template.id,
            'parameters': {}
        }
        
        response = self.client.post(
            '/api/reports/reports/',
            report_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
    
    def test_report_templates_list(self):
        """Test listing report templates."""
        response = self.client.get('/api/reports/templates/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Template')
    
    def test_report_templates_filter_active(self):
        """Test filtering report templates by active status."""
        # Create inactive template
        ReportTemplate.objects.create(
            name='Inactive Template',
            template_type='custom',
            template_content={},
            is_active=False
        )
        
        response = self.client.get('/api/reports/templates/?is_active=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_active'])
    
    def test_report_templates_filter_by_type(self):
        """Test filtering report templates by type."""
        # Create different type template
        ReportTemplate.objects.create(
            name='Threat Analysis Template',
            template_type='threat_analysis',
            template_content={},
            is_active=True
        )
        
        response = self.client.get('/api/reports/templates/?template_type=security_summary')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['template_type'], 'security_summary')
    
    def test_report_download(self):
        """Test downloading a report file."""
        # Create a temporary file to simulate report file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as temp_file:
            temp_file.write('Test PDF content')
            temp_file_path = temp_file.name
        
        try:
            # Update report with actual file path
            self.report.file_path = temp_file_path
            self.report.save()
            
            response = self.client.get(f'/api/reports/reports/{self.report.id}/download/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('Content-Disposition', response.headers)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_report_download_not_found(self):
        """Test downloading a report with missing file."""
        # Report with non-existent file path
        self.report.file_path = '/non/existent/file.pdf'
        self.report.save()
        
        response = self.client.get(f'/api/reports/reports/{self.report.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_report_download_no_file_path(self):
        """Test downloading a report without file path."""
        # Report without file path
        self.report.file_path = None
        self.report.save()
        
        response = self.client.get(f'/api/reports/reports/{self.report.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_report_statistics(self):
        """Test retrieving report statistics."""
        response = self.client.get('/api/reports/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reports', response.data)
        self.assertIn('by_status', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('recent_reports', response.data)
        
        self.assertEqual(response.data['total_reports'], 1)
        self.assertEqual(response.data['by_status']['completed'], 1)
        self.assertEqual(response.data['by_type']['security_summary'], 1)


class ScanReportGeneratorTest(TestCase):
    """Test cases for scan report generation."""
    
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
        
        # Create test threats
        self.scan_threat = ScanThreat.objects.create(
            scan_result=self.scan_result,
            name='Test.Virus',
            threat_type='virus',
            description='Test virus description',
            detection_engine='clamav',
            severity='high'
        )
        
        self.report_generator = ReportGenerator()
    
    def test_generate_scan_report_json(self):
        """Test generating scan report in JSON format."""
        report_data = self.report_generator.generate_scan_report(
            self.scan_result,
            format='json'
        )
        
        self.assertIsInstance(report_data, dict)
        self.assertEqual(report_data['scan_id'], str(self.scan_result.id))
        self.assertEqual(report_data['file_name'], 'test.exe')
        self.assertEqual(report_data['scan_status'], 'completed')
        self.assertEqual(report_data['threat_level'], 'high')
        self.assertIn('threats', report_data)
        self.assertEqual(len(report_data['threats']), 1)
    
    def test_generate_scan_report_with_threats(self):
        """Test generating scan report with threat details."""
        report_data = self.report_generator.generate_scan_report(
            self.scan_result,
            format='json',
            include_threats=True
        )
        
        self.assertIn('threats', report_data)
        threat_data = report_data['threats'][0]
        self.assertEqual(threat_data['name'], 'Test.Virus')
        self.assertEqual(threat_data['threat_type'], 'virus')
        self.assertEqual(threat_data['severity'], 'high')
        self.assertEqual(threat_data['detection_engine'], 'clamav')
    
    def test_generate_scan_report_summary(self):
        """Test generating scan report summary."""
        summary = self.report_generator.generate_scan_summary(
            [self.scan_result]
        )
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['total_scans'], 1)
        self.assertEqual(summary['completed_scans'], 1)
        self.assertEqual(summary['threats_found'], 1)
        self.assertIn('threat_levels', summary)
        self.assertEqual(summary['threat_levels']['high'], 1)
    
    def test_generate_user_scan_history(self):
        """Test generating user scan history report."""
        history = self.report_generator.generate_user_scan_history(
            self.user,
            days=30
        )
        
        self.assertIsInstance(history, dict)
        self.assertEqual(history['user_email'], 'test@example.com')
        self.assertEqual(history['total_scans'], 1)
        self.assertIn('scans', history)
        self.assertEqual(len(history['scans']), 1)
    
    def test_export_scan_report_csv(self):
        """Test exporting scan report to CSV format."""
        csv_data = self.report_generator.export_to_csv([self.scan_result])
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('file_name,scan_status,threat_level', csv_data)
        self.assertIn('test.exe,completed,high', csv_data)


class ThreatMapReportGeneratorTest(TestCase):
    """Test cases for threat map report generation."""
    
    def setUp(self):
        # Create test threat events
        self.threat_event1 = ThreatEvent.objects.create(
            threat_type='malware',
            severity='high',
            ip_address='192.168.1.100',
            country='US',
            city='New York',
            latitude=40.7128,
            longitude=-74.0060,
            description='Malware detected'
        )
        
        self.threat_event2 = ThreatEvent.objects.create(
            threat_type='phishing',
            severity='medium',
            ip_address='10.0.0.50',
            country='CA',
            city='Toronto',
            latitude=43.6532,
            longitude=-79.3832,
            description='Phishing attempt'
        )
        
        # Create global threat stats
        self.global_stats = GlobalThreatStats.objects.create(
            total_threats=100,
            active_threats=25,
            resolved_threats=75,
            high_severity_threats=10,
            medium_severity_threats=40,
            low_severity_threats=50
        )
        
        self.report_generator = ThreatMapReportGenerator()
    
    def test_generate_threat_map_report_json(self):
        """Test generating threat map report in JSON format."""
        report_data = self.report_generator.generate_threat_map_report(
            format='json'
        )
        
        self.assertIsInstance(report_data, dict)
        self.assertIn('threat_events', report_data)
        self.assertIn('global_stats', report_data)
        self.assertEqual(len(report_data['threat_events']), 2)
    
    def test_generate_threat_events_by_country(self):
        """Test generating threat events grouped by country."""
        country_data = self.report_generator.generate_threats_by_country()
        
        self.assertIsInstance(country_data, dict)
        self.assertIn('US', country_data)
        self.assertIn('CA', country_data)
        self.assertEqual(country_data['US']['count'], 1)
        self.assertEqual(country_data['CA']['count'], 1)
    
    def test_generate_threat_events_by_type(self):
        """Test generating threat events grouped by type."""
        type_data = self.report_generator.generate_threats_by_type()
        
        self.assertIsInstance(type_data, dict)
        self.assertIn('malware', type_data)
        self.assertIn('phishing', type_data)
        self.assertEqual(type_data['malware']['count'], 1)
        self.assertEqual(type_data['phishing']['count'], 1)
    
    def test_generate_threat_timeline(self):
        """Test generating threat timeline data."""
        timeline = self.report_generator.generate_threat_timeline(
            days=7
        )
        
        self.assertIsInstance(timeline, dict)
        self.assertIn('timeline', timeline)
        self.assertIn('total_events', timeline)
        self.assertEqual(timeline['total_events'], 2)
    
    def test_generate_global_threat_summary(self):
        """Test generating global threat summary."""
        summary = self.report_generator.generate_global_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['total_threats'], 100)
        self.assertEqual(summary['active_threats'], 25)
        self.assertEqual(summary['resolved_threats'], 75)
        self.assertIn('severity_breakdown', summary)


class ReportIntegrationTest(TestCase):
    """Test cases for report integration functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.scan_result = ScanResult.objects.create(
            user=self.user,
            file_name='integration_test.exe',
            file_size=2048,
            file_hash='integration123',
            scan_status='completed',
            threat_level='medium'
        )
        
        self.threat_event = ThreatEvent.objects.create(
            threat_type='virus',
            severity='medium',
            ip_address='203.0.113.1',
            country='GB',
            city='London',
            latitude=51.5074,
            longitude=-0.1278,
            description='Virus detected in network traffic'
        )
    
    def test_combined_security_report(self):
        """Test generating combined security report with scan and threat data."""
        scan_generator = ReportGenerator()
        threat_generator = ThreatMapReportGenerator()
        
        scan_data = scan_generator.generate_scan_report(self.scan_result)
        threat_data = threat_generator.generate_threat_map_report()
        
        combined_report = {
            'report_type': 'security_summary',
            'generated_at': datetime.now().isoformat(),
            'scan_data': scan_data,
            'threat_data': threat_data
        }
        
        self.assertIn('scan_data', combined_report)
        self.assertIn('threat_data', combined_report)
        self.assertEqual(combined_report['scan_data']['file_name'], 'integration_test.exe')
        self.assertGreaterEqual(len(combined_report['threat_data']['threat_events']), 1)
    
    def test_user_security_dashboard_data(self):
        """Test generating data for user security dashboard."""
        scan_generator = ReportGenerator()
        
        dashboard_data = {
            'user_scans': scan_generator.generate_user_scan_history(self.user, days=30),
            'recent_threats': ThreatEvent.objects.filter(
                timestamp__gte=datetime.now() - timedelta(days=7)
            ).count(),
            'scan_summary': scan_generator.generate_scan_summary([self.scan_result])
        }
        
        self.assertIn('user_scans', dashboard_data)
        self.assertIn('recent_threats', dashboard_data)
        self.assertIn('scan_summary', dashboard_data)
        self.assertEqual(dashboard_data['user_scans']['total_scans'], 1)


class ReportAPITest(APITestCase):
    """Test cases for report-related API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test scan result
        self.scan_result = ScanResult.objects.create(
            user=self.user,
            file_name='api_test.exe',
            file_size=1024,
            file_hash='api123',
            scan_status='completed',
            threat_level='low'
        )
    
    def test_get_scan_report(self):
        """Test retrieving scan report via API."""
        response = self.client.get(f'/api/scanner/scans/{self.scan_result.id}/report/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scan_id', response.data)
        self.assertEqual(response.data['file_name'], 'api_test.exe')
    
    def test_get_user_scan_history(self):
        """Test retrieving user scan history via API."""
        response = self.client.get('/api/scanner/scans/history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_scans', response.data)
        self.assertEqual(response.data['total_scans'], 1)
    
    def test_get_threat_map_data(self):
        """Test retrieving threat map data via API."""
        response = self.client.get('/api/threatmap/events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to report endpoints."""
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/scanner/scans/{self.scan_result.id}/report/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)