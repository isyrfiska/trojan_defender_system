from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, F
from datetime import datetime, timedelta
import logging
from django.conf import settings
from trojan_defender.view_cache import cache_dashboard_data

from .models import ThreatIntelligence, ThreatEvent, ThreatStatistics
from .serializers import (
    ThreatIntelligenceSerializer, ThreatEventSerializer,
    ThreatStatisticsSerializer, ThreatMapDataSerializer,
    DashboardStatsSerializer
)
from .external_api import ThreatIntelligenceUpdater

logger = logging.getLogger(__name__)


class ThreatIntelligenceListView(generics.ListAPIView):
    """List all threat intelligence data"""
    queryset = ThreatIntelligence.objects.all()
    serializer_class = ThreatIntelligenceSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by malicious status
        is_malicious = self.request.query_params.get('malicious')
        if is_malicious is not None:
            queryset = queryset.filter(is_malicious=is_malicious.lower() == 'true')
        
        # Filter by country
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country_code=country.upper())
        
        # Filter by confidence threshold
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                queryset = queryset.filter(abuse_confidence__gte=int(min_confidence))
            except ValueError:
                pass
        
        return queryset


class ThreatEventListView(generics.ListAPIView):
    """List threat events"""
    queryset = ThreatEvent.objects.all()
    serializer_class = ThreatEventSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by date range
        days = self.request.query_params.get('days', 7)
        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(detected_at__gte=start_date)
        except ValueError:
            pass
        
        return queryset


@cache_dashboard_data  # Use custom view-level caching
@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Get dashboard statistics for threat intelligence."""
    try:
        logger.info(f"Retrieving dashboard stats for user {request.user.id}")
        
        # Check if we have cached statistics in ThreatStatistics model
        try:
            cached_stats = ThreatStatistics.objects.latest('created_at')
            if cached_stats.created_at > timezone.now() - timedelta(minutes=5):
                logger.info("Using cached threat statistics from database")
                return Response({
                    'total_threats': cached_stats.total_threats,
                    'new_threats_today': cached_stats.new_threats_today,
                    'high_confidence_threats': cached_stats.high_confidence_threats,
                    'affected_countries': cached_stats.affected_countries,
                    'top_threat_types': cached_stats.top_threat_types,
                    'threat_trend': cached_stats.threat_trend
                })
        except ThreatStatistics.DoesNotExist:
            pass
        
        # Calculate fresh statistics with optimized queries
        today = timezone.now().date()
        
        # Single aggregated query for threat counts
        threat_stats = ThreatIntelligence.objects.aggregate(
            total_threats=Count('id'),
            high_confidence_threats=Count('id', filter=Q(confidence_score__gte=0.8)),
            new_threats_today=Count('id', filter=Q(created_at__date=today))
        )
        
        # Optimized query for affected countries
        affected_countries = ThreatEvent.objects.values('country').distinct().count()
        
        # Optimized query for top threat types
        top_threat_types = list(
            ThreatIntelligence.objects
            .values('threat_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Optimized query for threat trend (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        threat_trend = list(
            ThreatIntelligence.objects
            .filter(created_at__gte=seven_days_ago)
            .extra(select={'day': 'date(created_at)'})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        response_data = {
            'total_threats': threat_stats['total_threats'] or 0,
            'new_threats_today': threat_stats['new_threats_today'] or 0,
            'high_confidence_threats': threat_stats['high_confidence_threats'] or 0,
            'affected_countries': affected_countries,
            'top_threat_types': top_threat_types,
            'threat_trend': threat_trend
        }
        
        # Update cached statistics in database
        ThreatStatistics.objects.create(
            total_threats=response_data['total_threats'],
            new_threats_today=response_data['new_threats_today'],
            high_confidence_threats=response_data['high_confidence_threats'],
            affected_countries=response_data['affected_countries'],
            top_threat_types=response_data['top_threat_types'],
            threat_trend=response_data['threat_trend']
        )
        
        logger.info(f"Dashboard stats retrieved successfully for user {request.user.id}")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard stats for user {request.user.id}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve dashboard statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def threat_map_data(request):
    """Get threat map visualization data"""
    try:
        # Get recent threat events with location data
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        events = ThreatEvent.objects.filter(
            detected_at__gte=start_date,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('threat_intelligence')
        
        # Group by location and aggregate
        location_data = {}
        for event in events:
            key = f"{event.latitude},{event.longitude}"
            if key not in location_data:
                location_data[key] = {
                    'ip_address': event.threat_intelligence.ip_address,
                    'country_code': event.threat_intelligence.country_code or 'XX',
                    'country_name': event.threat_intelligence.country_name or 'Unknown',
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                    'threat_count': 0,
                    'severity': 'low',
                    'last_seen': event.detected_at
                }
            
            location_data[key]['threat_count'] += 1
            
            # Update severity to highest seen
            if event.severity == 'critical':
                location_data[key]['severity'] = 'critical'
            elif event.severity == 'high' and location_data[key]['severity'] not in ['critical']:
                location_data[key]['severity'] = 'high'
            elif event.severity == 'medium' and location_data[key]['severity'] not in ['critical', 'high']:
                location_data[key]['severity'] = 'medium'
            
            # Update last seen to most recent
            if event.detected_at > location_data[key]['last_seen']:
                location_data[key]['last_seen'] = event.detected_at
        
        # Convert to list and serialize
        map_data = list(location_data.values())
        serializer = ThreatMapDataSerializer(map_data, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting threat map data: {e}")
        return Response(
            {'error': 'Failed to retrieve threat map data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def update_threat_data(request):
    """Manually trigger threat data update"""
    try:
        updater = ThreatIntelligenceUpdater()

        # Update from AbuseIPDB blacklist
        success = updater.update_from_abuseipdb_blacklist()

        if success:
            # Update daily statistics
            updater.update_daily_statistics()

            return Response({
                'message': 'Threat data updated successfully',
                'timestamp': timezone.now().isoformat()
            })
        else:
            # Gracefully handle missing API key or external API issues in dev/test
            if not getattr(settings, 'ABUSEIPDB_API_KEY', None):
                # Still update daily statistics from existing data
                updater.update_daily_statistics()
                return Response({
                    'message': 'Threat data update skipped: AbuseIPDB API key not configured',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_202_ACCEPTED)
            # For other external API failures, return Accepted to indicate retry can occur
            return Response(
                {'message': 'Threat data update deferred due to external API issues'},
                status=status.HTTP_202_ACCEPTED
            )

    except Exception as e:
        logger.error(f"Error updating threat data: {e}")
        # In dev, respond with 202 to avoid hard failure while logging the issue
        return Response(
            {'message': 'Threat data update encountered an error but was deferred'},
            status=status.HTTP_202_ACCEPTED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def check_ips(request):
    """Check specific IPs against threat intelligence"""
    try:
        ip_list = request.data.get('ips', [])
        if not ip_list:
            return Response(
                {'error': 'No IPs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updater = ThreatIntelligenceUpdater()
        results = updater.check_specific_ips(ip_list)
        
        serializer = ThreatIntelligenceSerializer(results, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error checking IPs: {e}")
        return Response(
            {'error': 'Failed to check IPs'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def threat_statistics(request):
    """Get threat statistics for a date range"""
    try:
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        stats = ThreatStatistics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        serializer = ThreatStatisticsSerializer(stats, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting threat statistics: {e}")
        return Response(
            {'error': 'Failed to retrieve threat statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
