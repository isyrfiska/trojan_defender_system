from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
import logging
from .models import ThreatEvent, GlobalThreatStats
from .serializers import ThreatEventSerializer, ThreatEventCreateSerializer, GlobalThreatStatsSerializer, ThreatMapDataSerializer
from .reports import ThreatMapReportGenerator
from trojan_defender.exceptions import ValidationException, ScannerException
from trojan_defender.cache_utils import cache_api_response, cache_threat_data, default_cache
from .services import ThreatMapService

logger = logging.getLogger('api')


class ThreatEventPagination(PageNumberPagination):
    """Custom pagination for threat events."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ThreatEventViewSet(viewsets.ModelViewSet):
    """ViewSet for threat events with enhanced real-time capabilities."""
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ThreatEventPagination
    
    def get_queryset(self):
        try:
            # Regular users can only see their own threat events
            if not self.request.user.is_staff:
                return ThreatEvent.objects.filter(user=self.request.user)
            # Staff can see all threat events
            return ThreatEvent.objects.all()
        except Exception as e:
            logger.error(f"Error retrieving threat events: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve threat events", details=str(e))
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ThreatEventCreateSerializer
        return ThreatEventSerializer
    
    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Threat event created by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error creating threat event: {str(e)}", exc_info=True)
            raise ScannerException("Failed to create threat event", details=str(e))
    
    @action(detail=False, methods=['get'])
    def realtime_data(self, request):
        """Get real-time threat data with advanced filtering and pagination."""
        try:
            # Parse query parameters
            days = int(request.query_params.get('days', 1))
            threat_type = request.query_params.get('threat_type', '')
            severity = request.query_params.get('severity', '')
            country = request.query_params.get('country', '')
            last_update = request.query_params.get('last_update', '')
            
            # Validate parameters
            if days < 1 or days > 365:
                raise ValidationException("Days parameter must be between 1 and 365")
            
            # Build query
            since = timezone.now() - timedelta(days=days)
            queryset = self.get_queryset().filter(timestamp__gte=since)
            
            # Apply filters
            if threat_type:
                queryset = queryset.filter(threat_type=threat_type)
            if severity:
                queryset = queryset.filter(severity=severity)
            if country:
                queryset = queryset.filter(country__icontains=country)
            if last_update:
                try:
                    last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    queryset = queryset.filter(timestamp__gt=last_update_dt)
                except ValueError:
                    raise ValidationException("Invalid last_update format")
            
            # Order by timestamp for real-time updates
            queryset = queryset.order_by('-timestamp')
            
            # Serialize data
            serializer = ThreatEventSerializer(queryset, many=True)
            
            # Prepare response with metadata
            response_data = {
                'threats': serializer.data,
                'total_count': queryset.count(),
                'last_update': timezone.now().isoformat(),
                'filters_applied': {
                    'days': days,
                    'threat_type': threat_type,
                    'severity': severity,
                    'country': country
                }
            }
            
            return Response(response_data)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving real-time threat data: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve real-time threat data", details=str(e))
    
    @action(detail=False, methods=['get'])
    def map_data(self, request):
        """Get formatted data for threat map visualization with heat mapping."""
        try:
            # Validate days parameter
            try:
                days = int(request.query_params.get('days', 30))
                if days < 1 or days > 365:
                    raise ValidationException("Days parameter must be between 1 and 365")
            except ValueError:
                raise ValidationException("Days parameter must be a valid integer")
            
            # Additional filters
            threat_type = request.query_params.get('threat_type', '')
            severity = request.query_params.get('severity', '')
            
            # Create cache key based on user and parameters
            cache_key = f"threat_map_data:user_{request.user.id}:days_{days}:type_{threat_type}:sev_{severity}"
            
            # Try to get from cache first
            cached_data = default_cache.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached threat map data for user {request.user.id}")
                return Response(cached_data)
            
            since = timezone.now() - timedelta(days=days)
            
            threats = self.get_queryset().filter(timestamp__gte=since)
            
            # Apply additional filters
            if threat_type:
                threats = threats.filter(threat_type=threat_type)
            if severity:
                threats = threats.filter(severity=severity)
            
            # Format data for map with heat mapping
            map_data = []
            heat_data = []
            
            for threat in threats:
                if threat.latitude and threat.longitude:
                    threat_data = {
                        'id': str(threat.id),
                        'lat': float(threat.latitude),
                        'lng': float(threat.longitude),
                        'threat_type': threat.threat_type,
                        'severity': threat.severity,
                        'timestamp': threat.timestamp.isoformat(),
                        'country': threat.country,
                        'city': threat.city,
                        'description': threat.description,
                        'file_name': threat.file_name,
                        'ip_address': threat.ip_address
                    }
                    map_data.append(threat_data)
                    
                    # Add to heat map data with intensity based on severity
                    intensity = {
                        'low': 0.3,
                        'medium': 0.6,
                        'high': 0.8,
                        'critical': 1.0
                    }.get(threat.severity, 0.5)
                    
                    heat_data.append({
                        'lat': float(threat.latitude),
                        'lng': float(threat.longitude),
                        'intensity': intensity
                    })
            
            # Get threat statistics for the period
            threat_stats = threats.values('threat_type').annotate(count=Count('id'))
            severity_stats = threats.values('severity').annotate(count=Count('id'))
            country_stats = threats.values('country').annotate(count=Count('id')).order_by('-count')[:10]
            
            response_data = {
                'threats': map_data,
                'heat_data': heat_data,
                'total_count': len(map_data),
                'statistics': {
                    'by_type': list(threat_stats),
                    'by_severity': list(severity_stats),
                    'by_country': list(country_stats)
                },
                'date_range': {
                    'start': since.isoformat(),
                    'end': timezone.now().isoformat()
                },
                'filters': {
                    'threat_type': threat_type,
                    'severity': severity
                }
            }
            
            # Cache the response for 5 minutes
            default_cache.cache.set(cache_key, response_data, 300)
            
            return Response(response_data)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving threat map data: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve threat map data", details=str(e))
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Generate threat map report with enhanced performance."""
        try:
            # Validate parameters
            try:
                days = int(request.query_params.get('days', 30))
                if days < 1 or days > 365:
                    raise ValidationException("Days parameter must be between 1 and 365")
            except ValueError:
                raise ValidationException("Days parameter must be a valid integer")
            
            format_type = request.query_params.get('format', 'json')
            if format_type not in ['json', 'pdf', 'csv']:
                raise ValidationException("Format must be json, pdf, or csv")
            
            # Use cached data if available
            cache_key = f"threat_report:user_{request.user.id}:days_{days}:format_{format_type}"
            cached_report = default_cache.cache.get(cache_key)
            if cached_report:
                logger.debug(f"Returning cached threat report for user {request.user.id}")
                return Response(cached_report)
            
            # Generate report
            report_generator = ThreatMapReportGenerator()
            
            # Get optimized queryset with select_related and prefetch_related
            since = timezone.now() - timedelta(days=days)
            queryset = self.get_queryset().filter(timestamp__gte=since).select_related('user', 'scan_result')
            
            report_data = report_generator.generate_report(
                queryset=queryset,
                format_type=format_type,
                user=request.user,
                days=days
            )
            
            # Cache the report for 1 hour
            default_cache.cache.set(cache_key, report_data, 3600)
            
            logger.info(f"Generated threat report for user {request.user.id}: {format_type} format, {days} days")
            
            return Response(report_data)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error generating threat report: {str(e)}", exc_info=True)
            raise ScannerException("Failed to generate threat report", details=str(e))


class ThreatMapViewSet(viewsets.ViewSet):
    """ViewSet for threat map data with performance optimizations."""
    
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Get threat map overview with optimized queries."""
        try:
            # Use ThreatMapService to get the latest stats
            stats = ThreatMapService.get_latest_stats()
            return Response(stats)
                
        except Exception as e:
            logger.error(f"Error retrieving threat map overview: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve threat map overview", details=str(e))
                
        except Exception as e:
            logger.error(f"Error retrieving threat map overview: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve threat map overview", details=str(e))
    
    @action(detail=False, methods=['get'])
    def data(self, request):
        """Get threat map data with performance optimizations."""
        try:
            # Parse and validate parameters
            days = int(request.query_params.get('days', 30))
            page_size = min(int(request.query_params.get('page_size', 1000)), 5000)  # Limit max page size
            threat_type = request.query_params.get('threat_type', '')
            severity = request.query_params.get('severity', '')
            
            # Create optimized cache key
            cache_key = f"threat_map_data:days_{days}:type_{threat_type}:sev_{severity}:size_{page_size}"
            
            # Try to get from cache first
            cached_data = default_cache.cache.get(cache_key)
            if cached_data:
                logger.debug("Returning cached threat map data")
                return Response(cached_data)
            
            # Build optimized query
            since = timezone.now() - timedelta(days=days)
            
            # Use database indexes efficiently
            queryset = ThreatEvent.objects.filter(
                timestamp__gte=since,
                latitude__isnull=False,
                longitude__isnull=False
            ).select_related('user').only(
                'id', 'threat_type', 'severity', 'timestamp', 
                'latitude', 'longitude', 'country', 'city', 'description'
            )
            
            # Apply filters
            if threat_type:
                queryset = queryset.filter(threat_type=threat_type)
            if severity:
                queryset = queryset.filter(severity=severity)
            
            # Limit results and order efficiently
            queryset = queryset.order_by('-timestamp')[:page_size]
            
            # Serialize efficiently
            threat_data = []
            for threat in queryset:
                threat_data.append({
                    'id': str(threat.id),
                    'lat': float(threat.latitude),
                    'lng': float(threat.longitude),
                    'threat_type': threat.threat_type,
                    'severity': threat.severity,
                    'timestamp': threat.timestamp.isoformat(),
                    'country': threat.country,
                    'city': threat.city,
                    'description': threat.description[:100] if threat.description else ''  # Truncate for performance
                })
            
            # Get aggregated statistics efficiently
            stats_queryset = ThreatEvent.objects.filter(timestamp__gte=since)
            if threat_type:
                stats_queryset = stats_queryset.filter(threat_type=threat_type)
            if severity:
                stats_queryset = stats_queryset.filter(severity=severity)
            
            # Use database aggregation
            threat_stats = stats_queryset.values('threat_type').annotate(count=Count('id'))
            severity_stats = stats_queryset.values('severity').annotate(count=Count('id'))
            country_stats = stats_queryset.values('country').annotate(count=Count('id')).order_by('-count')[:10]
            
            response_data = {
                'threats': threat_data,
                'total_count': len(threat_data),
                'statistics': {
                    'by_type': list(threat_stats),
                    'by_severity': list(severity_stats),
                    'by_country': list(country_stats)
                },
                'date_range': {
                    'start': since.isoformat(),
                    'end': timezone.now().isoformat()
                },
                'performance_info': {
                    'cached': False,
                    'query_time': timezone.now().isoformat(),
                    'result_count': len(threat_data)
                }
            }
            
            # Cache for 2 minutes (shorter cache for real-time data)
            default_cache.cache.set(cache_key, response_data, 120)
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error retrieving threat map data: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve threat map data", details=str(e))
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Generate optimized threat map report."""
        try:
            # Use async task for large reports
            days = int(request.query_params.get('days', 30))
            format_type = request.query_params.get('format', 'json')
            
            if days > 90 or format_type == 'pdf':
                # For large reports, use background task
                from .tasks import generate_threat_report_async
                
                task = generate_threat_report_async.delay(
                    user_id=request.user.id,
                    days=days,
                    format_type=format_type
                )
                
                return Response({
                    'task_id': task.id,
                    'status': 'processing',
                    'message': 'Report generation started. Check status with task_id.'
                })
            else:
                # For small reports, generate synchronously with caching
                cache_key = f"threat_report:user_{request.user.id}:days_{days}:format_{format_type}"
                cached_report = default_cache.cache.get(cache_key)
                
                if cached_report:
                    return Response(cached_report)
                
                # Generate report with optimized queries
                report_generator = ThreatMapReportGenerator()
                since = timezone.now() - timedelta(days=days)
                
                # Use efficient query with minimal data
                queryset = ThreatEvent.objects.filter(
                    timestamp__gte=since
                ).select_related('user').only(
                    'threat_type', 'severity', 'timestamp', 'country'
                )
                
                report_data = report_generator.generate_summary_report(
                    queryset=queryset,
                    format_type=format_type
                )
                
                # Cache for 1 hour
                default_cache.cache.set(cache_key, report_data, 3600)
                
                return Response(report_data)
                
        except Exception as e:
            logger.error(f"Error generating threat report: {str(e)}", exc_info=True)
            raise ScannerException("Failed to generate threat report", details=str(e))
    
    def _get_threats_by_type(self, queryset):
        """Get threat distribution by type with database aggregation."""
        return queryset.values('threat_type').annotate(count=Count('id')).order_by('-count')

    def _get_threats_by_severity(self, queryset):
        """Get threat distribution by severity with database aggregation."""
        return queryset.values('severity').annotate(count=Count('id')).order_by('-count')

    def _get_threats_by_country(self, queryset):
        """Get threat distribution by country with database aggregation."""
        return queryset.values('country').annotate(count=Count('id')).order_by('-count')[:20]


class GlobalThreatStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for global threat statistics with caching."""
    
    queryset = GlobalThreatStats.objects.all().order_by('-date')
    serializer_class = GlobalThreatStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ThreatEventPagination

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest global threat statistics with caching."""
        try:
            cache_key = "global_threat_stats_latest"
            cached_stats = default_cache.cache.get(cache_key)
            
            if cached_stats:
                return Response(cached_stats)
            
            # Get latest stats efficiently
            latest_stats = self.queryset.first()
            
            if latest_stats:
                serializer = self.get_serializer(latest_stats)
                stats_data = serializer.data
                
                # Cache for 10 minutes
                default_cache.cache.set(cache_key, stats_data, 600)
                
                return Response(stats_data)
            else:
                return Response({'message': 'No global threat statistics available'})
                
        except Exception as e:
            logger.error(f"Error retrieving latest global threat statistics: {str(e)}", exc_info=True)
            raise ScannerException("Failed to retrieve latest global threat statistics", details=str(e))