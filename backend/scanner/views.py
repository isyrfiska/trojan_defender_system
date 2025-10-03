import os
import hashlib
import datetime
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from celery.result import AsyncResult
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging
from .models import ScanResult, ScanThreat, YaraRule, ScanStatistics
from .serializers import (
    ScanResultSerializer, ScanResultListSerializer, FileUploadSerializer,
    ScanThreatSerializer, YaraRuleSerializer, ScanStatisticsSerializer
)
from .tasks import scan_file
from .reports import ReportGenerator
from django.contrib.auth import get_user_model
from trojan_defender.exceptions import (
    ScannerException, FileUploadException, ValidationException
)
from trojan_defender.cache_utils import cache_scan_results, cache_api_response, default_cache
from trojan_defender.view_cache import cache_viewset_action, cache_stats_endpoint

logger = logging.getLogger('scanner')


class ScanResultViewSet(viewsets.ModelViewSet):
    """ViewSet for scan results."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ScanResult.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ScanResultListSerializer
        return ScanResultSerializer
    
    @action(detail=True, methods=['get'])
    def threats(self, request, pk=None):
        """Get threats for a specific scan result."""
        try:
            scan_result = self.get_object()
            threats = scan_result.threats.all()
            serializer = ScanThreatSerializer(threats, many=True)
            
            logger.info(
                f"Retrieved {threats.count()} threats for scan {scan_result.id}",
                extra={'user': request.user.email, 'scan_id': scan_result.id}
            )
            
            return Response(serializer.data)
        except Exception as e:
            logger.error(
                f"Error retrieving threats for scan {pk}: {str(e)}",
                extra={'user': request.user.email, 'scan_id': pk},
                exc_info=True
            )
            raise ScannerException(
                "Failed to retrieve scan threats",
                error_code="THREATS_RETRIEVAL_ERROR",
                details={'scan_id': pk}
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get the current status of a scan."""
        try:
            scan_result = self.get_object()
            
            response_data = {
                'status': scan_result.status,
                'status_display': scan_result.get_status_display(),
                'threat_level': scan_result.threat_level,
                'threat_level_display': scan_result.get_threat_level_display(),
                'scan_date': scan_result.scan_date,
                'scan_duration': scan_result.scan_duration
            }
            
            logger.info(
                f"Status check for scan {scan_result.id}: {scan_result.status}",
                extra={'user': request.user.email, 'scan_id': scan_result.id}
            )
            
            return Response(response_data)
        except Exception as e:
            logger.error(
                f"Error checking status for scan {pk}: {str(e)}",
                extra={'user': request.user.email, 'scan_id': pk},
                exc_info=True
            )
            raise ScannerException(
                "Failed to retrieve scan status",
                error_code="STATUS_RETRIEVAL_ERROR",
                details={'scan_id': pk}
            )
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Generate and download scan report in PDF or JSON format."""
        try:
            scan_result = self.get_object()
            report_format = request.query_params.get('format', 'pdf').lower()
            
            if report_format not in ['pdf', 'json']:
                raise ValidationException(
                    "Invalid report format",
                    error_code="INVALID_REPORT_FORMAT",
                    details={'supported_formats': ['pdf', 'json'], 'requested_format': report_format}
                )
            
            logger.info(
                f"Generating {report_format} report for scan {scan_result.id}",
                extra={'user': request.user.email, 'scan_id': scan_result.id, 'format': report_format}
            )
            
            generator = ReportGenerator(scan_result)
            
            if report_format == 'pdf':
                pdf_buffer = generator.generate_pdf_report()
                response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="scan_report_{scan_result.id}.pdf"'
                return response
            
            elif report_format == 'json':
                json_report = generator.generate_json_report()
                response = HttpResponse(json_report, content_type='application/json')
                response['Content-Disposition'] = f'attachment; filename="scan_report_{scan_result.id}.json"'
                return response
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(
                f"Error generating {report_format} report for scan {pk}: {str(e)}",
                extra={'user': request.user.email, 'scan_id': pk, 'format': report_format},
                exc_info=True
            )
            raise ScannerException(
                "Failed to generate scan report",
                error_code="REPORT_GENERATION_ERROR",
                details={'scan_id': pk, 'format': report_format}
            )


@method_decorator(ratelimit(key='user', rate='10/h', method='POST', block=True), name='create')
class FileUploadView(viewsets.ViewSet):
    """ViewSet for file uploads and scanning."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request):
        """Upload and scan a file."""
        try:
            logger.info(f"File upload initiated by user {request.user.id}")
            
            serializer = FileUploadSerializer(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Invalid file upload data from user {request.user.id}: {serializer.errors}")
                raise ValidationException("Invalid file data provided", details=serializer.errors)
            
            uploaded_file = serializer.validated_data['file']
            logger.info(f"Processing file upload: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(uploaded_file)
            logger.debug(f"File hash calculated: {file_hash}")
            
            # Create scan result record
            scan_result = ScanResult.objects.create(
                user=request.user,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=uploaded_file.content_type,
                file_hash=file_hash,
                status=ScanResult.ScanStatus.PENDING
            )
            logger.info(f"Scan result created with ID: {scan_result.id}")
            
            # Save file to storage
            storage_path = self._save_file(uploaded_file, scan_result.id)
            scan_result.storage_path = storage_path
            scan_result.save()
            logger.info(f"File saved to storage: {storage_path}")
            
            # Start scan task
            task = scan_file.delay(str(scan_result.id))
            logger.info(f"Scan task initiated with ID: {task.id}")
            
            # Return response
            return Response({
                'scan_id': scan_result.id,
                'task_id': task.id,
                'message': 'File uploaded successfully and scan initiated.'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"File upload failed for user {request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("File upload failed", details=str(e))
    
    def _calculate_file_hash(self, file):
        """Calculate SHA-256 hash of the file."""
        try:
            sha256 = hashlib.sha256()
            for chunk in file.chunks():
                sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {str(e)}", exc_info=True)
            raise ScannerException("Failed to calculate file hash", details=str(e))
    
    def _save_file(self, file, scan_id):
        """Save uploaded file to storage."""
        try:
            # Create directory structure based on date
            today = datetime.datetime.now()
            dir_path = os.path.join(
                settings.MEDIA_ROOT, 
                'uploads', 
                str(today.year),
                str(today.month).zfill(2),
                str(today.day).zfill(2),
                str(scan_id)
            )
            
            os.makedirs(dir_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(dir_path, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            return file_path
        except Exception as e:
            logger.error(f"Failed to save file for scan {scan_id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to save uploaded file", details=str(e))


class YaraRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for YARA rules."""
    
    serializer_class = YaraRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            # Regular users can only see their own rules
            if not self.request.user.is_staff:
                return YaraRule.objects.filter(created_by=self.request.user)
            # Staff can see all rules
            return YaraRule.objects.all()
        except Exception as e:
            logger.error(f"Failed to get YARA rules queryset for user {self.request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve YARA rules", details=str(e))
    
    def create(self, request, *args, **kwargs):
        """Create a new YARA rule."""
        try:
            logger.info(f"Creating YARA rule by user {request.user.id}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create YARA rule for user {request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to create YARA rule", details=str(e))
    
    def update(self, request, *args, **kwargs):
        """Update a YARA rule."""
        try:
            logger.info(f"Updating YARA rule {kwargs.get('pk')} by user {request.user.id}")
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update YARA rule for user {request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to update YARA rule", details=str(e))
    
    def destroy(self, request, *args, **kwargs):
        """Delete a YARA rule."""
        try:
            logger.info(f"Deleting YARA rule {kwargs.get('pk')} by user {request.user.id}")
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to delete YARA rule for user {request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to delete YARA rule", details=str(e))


class ScanStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for scan statistics."""
    
    serializer_class = ScanStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            # Only staff can see all statistics
            if not self.request.user.is_staff:
                return ScanStatistics.objects.none()
            return ScanStatistics.objects.all().order_by('-date')
        except Exception as e:
            logger.error(f"Failed to get scan statistics queryset for user {self.request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve scan statistics", details=str(e))
    
    @cache_stats_endpoint  # Use custom view-level caching
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics."""
        try:
            logger.info(f"Retrieving scan statistics summary for user {request.user.id}")
            
            # Optimized user statistics using aggregation
            user_scan_stats = ScanResult.objects.filter(user=request.user).aggregate(
                total_scans=Count('id'),
                clean_files=Count('id', filter=Q(threat_level=ScanResult.ThreatLevel.CLEAN)),
                infected_files=Count('id', filter=~Q(threat_level=ScanResult.ThreatLevel.CLEAN)),
                pending_scans=Count('id', filter=Q(status=ScanResult.ScanStatus.PENDING)),
                avg_scan_duration=Coalesce(Avg('scan_duration'), 0.0)
            )
            
            user_stats = {
                'total_scans': user_scan_stats['total_scans'] or 0,
                'clean_files': user_scan_stats['clean_files'] or 0,
                'infected_files': user_scan_stats['infected_files'] or 0,
                'pending_scans': user_scan_stats['pending_scans'] or 0,
                'avg_scan_duration': float(user_scan_stats['avg_scan_duration'] or 0.0)
            }
            
            response_data = user_stats
            
            # For staff - optimized global statistics
            if request.user.is_staff:
                User = get_user_model()
                
                # Single query for global scan statistics
                global_scan_stats = ScanResult.objects.aggregate(
                    total_scans=Count('id'),
                    clean_files=Count('id', filter=Q(threat_level=ScanResult.ThreatLevel.CLEAN)),
                    infected_files=Count('id', filter=~Q(threat_level=ScanResult.ThreatLevel.CLEAN)),
                    avg_scan_duration=Coalesce(Avg('scan_duration'), 0.0)
                )
                
                # Single query for threat count
                total_threats = ScanThreat.objects.count()
                
                # Single query for user count
                users_count = User.objects.count()
                
                global_stats = {
                    'total_scans': global_scan_stats['total_scans'] or 0,
                    'clean_files': global_scan_stats['clean_files'] or 0,
                    'infected_files': global_scan_stats['infected_files'] or 0,
                    'total_threats': total_threats,
                    'users_count': users_count,
                    'avg_scan_duration': float(global_scan_stats['avg_scan_duration'] or 0.0)
                }
                response_data = {'user': user_stats, 'global': global_stats}
                logger.info(f"Retrieved global statistics for staff user {request.user.id}")
            else:
                logger.info(f"Retrieved user statistics for user {request.user.id}")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Failed to retrieve scan statistics for user {request.user.id}: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve scan statistics", details=str(e))