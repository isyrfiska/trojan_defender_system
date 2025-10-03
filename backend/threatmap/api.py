from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import ThreatEvent, GlobalThreatStats, ThreatDataSource
from .services import ThreatDataFetcher, ThreatMapService
from .serializers import (
    ThreatEventSerializer, 
    GlobalThreatStatsSerializer,
    ThreatDataSourceSerializer
)


class ThreatMapViewSet(viewsets.ViewSet):
    """API endpoints for threat map data."""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get threat events with filtering by days, threat_type, severity, and country."""
        try:
            # Get days parameter with default of 30 days
            try:
                days = int(request.query_params.get('days', 30))
                days = max(1, min(days, 365))  # Between 1 and 365 days
            except ValueError:
                days = 30
                
            # Calculate the date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Build query filters
            query_filters = {'timestamp__gte': start_date}
            
            # Add optional filters if provided
            if threat_type := request.query_params.get('threat_type'):
                if threat_type.strip():
                    query_filters['threat_type'] = threat_type
                    
            if severity := request.query_params.get('severity'):
                if severity.strip():
                    query_filters['severity'] = severity
                    
            if country := request.query_params.get('country'):
                if country.strip():
                    query_filters['country'] = country
            
            # Query the database
            threats = ThreatEvent.objects.filter(**query_filters).order_by('-timestamp')[:1000]
            
            # Serialize the data
            serializer = ThreatEventSerializer(threats, many=True)
            
            return Response({
                'count': len(serializer.data),
                'results': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve threat data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
    @action(detail=False, methods=['GET'])
    def latest_threats(self, request):
        """Get the latest threat events with optional filtering."""
        try:
            # Extract filter parameters
            filters = {
                'threat_type': request.query_params.get('threat_type'),
                'severity': request.query_params.get('severity'),
                'country': request.query_params.get('country'),
                'time_range': request.query_params.get('time_range', 'last_month')
            }
            
            # Get limit parameter with default
            try:
                limit = int(request.query_params.get('limit', 100))
                limit = min(limit, 1000)  # Cap at 1000 to prevent excessive queries
            except ValueError:
                limit = 100
            
            # Get threats using the service
            threats = ThreatMapService.get_latest_threats(limit=limit, **filters)
            
            return Response({
                'count': len(threats),
                'results': threats
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve threat data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['GET'])
    def stats(self, request):
        """Get global threat statistics."""
        try:
            stats = ThreatMapService.get_latest_stats()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve threat statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['GET'])
    def stats_history(self, request):
        """Get historical threat statistics."""
        try:
            # Get days parameter with default
            try:
                days = int(request.query_params.get('days', 30))
                days = min(days, 365)  # Cap at 1 year
            except ValueError:
                days = 30
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get stats for the date range
            stats = GlobalThreatStats.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            # Serialize the data
            serializer = GlobalThreatStatsSerializer(stats, many=True)
            
            return Response({
                'count': len(serializer.data),
                'results': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve historical statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['POST'])
    def refresh_data(self, request):
        """Manually trigger data refresh from external sources."""
        try:
            # Check if user has permission
            if not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to perform this action.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create fetcher and fetch data
            fetcher = ThreatDataFetcher()
            results = fetcher.fetch_from_all_sources()
            
            return Response({
                'message': 'Data refresh completed successfully',
                'results': results
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to refresh threat data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThreatDataSourceViewSet(viewsets.ModelViewSet):
    """API endpoints for managing threat data sources."""
    queryset = ThreatDataSource.objects.all().order_by('priority')
    serializer_class = ThreatDataSourceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only staff users can see all sources
        if not self.request.user.is_staff:
            return ThreatDataSource.objects.none()
        return super().get_queryset()
    
    @action(detail=True, methods=['POST'])
    def test_connection(self, request, pk=None):
        """Test the connection to a data source."""
        try:
            # Get the data source
            source = self.get_object()
            
            # Create fetcher and attempt to fetch from this source
            fetcher = ThreatDataFetcher()
            
            try:
                # Just test the connection, don't save data
                response = fetcher.session.get(
                    source.api_endpoint,
                    headers={'Authorization': f'Bearer {source.api_key}'} if source.api_key else {},
                    timeout=10
                )
                
                if response.status_code == 200:
                    return Response({
                        'success': True,
                        'message': 'Connection successful',
                        'status_code': response.status_code
                    })
                else:
                    return Response({
                        'success': False,
                        'message': f'Connection failed with status code {response.status_code}',
                        'status_code': response.status_code
                    })
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Connection failed: {str(e)}',
                    'error': str(e)
                })
        except Exception as e:
            return Response(
                {'error': f'Failed to test connection: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )