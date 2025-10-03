import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta
from .models import ThreatEvent
from .serializers import ThreatEventSerializer
from urllib.parse import parse_qs

logger = logging.getLogger('websocket')


class ThreatMapConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time threat map updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            # Parse JWT token from query string and set authenticated user if provided
            try:
                qs_bytes = self.scope.get('query_string', b'')
                qs = parse_qs(qs_bytes.decode())
                token = (qs.get('token') or [None])[0]
                if token:
                    from rest_framework_simplejwt.tokens import AccessToken
                    from django.contrib.auth import get_user_model
                    access_token = AccessToken(token)
                    user_id = access_token['user_id']
                    User = get_user_model()
                    user = await database_sync_to_async(User.objects.get)(id=user_id)
                    self.scope['user'] = user
            except Exception as e:
                logger.warning(f"ThreatMap WS token parsing/validation failed: {e}")
                # If token parsing/validation fails, keep existing scope['user']
                pass

            # Check if user is authenticated
            user = self.scope.get("user")
            if not getattr(user, "is_authenticated", False):
                logger.warning("Unauthenticated user attempted to connect to threat map WebSocket")
                await self.close()
                return

            # Join threat map group
            self.group_name = f"threat_map_{user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"User {user.id} connected to threat map WebSocket")

            # Send initial data
            await self.send_initial_data()

        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}", exc_info=True)
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            logger.info(f"User disconnected from threat map WebSocket with code: {close_code}")
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {str(e)}", exc_info=True)
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            
            if message_type == 'get_threats':
                await self.handle_get_threats(data)
            elif message_type == 'subscribe_filters':
                await self.handle_subscribe_filters(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_get_threats(self, data):
        """Handle request for threat data."""
        try:
            filters = data.get('filters', {})
            days = filters.get('days', 1)
            threat_type = filters.get('threat_type', '')
            severity = filters.get('severity', '')
            
            threats = await self.get_filtered_threats(days, threat_type, severity)
            
            await self.send(text_data=json.dumps({
                'type': 'threat_data',
                'data': threats,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling get_threats: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to retrieve threat data'
            }))
    
    async def handle_subscribe_filters(self, data):
        """Handle subscription to filtered threat updates."""
        try:
            filters = data.get('filters', {})
            # Store filters for this connection (could be stored in Redis for persistence)
            self.filters = filters
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'filters': filters,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling subscribe_filters: {str(e)}", exc_info=True)
    
    async def send_initial_data(self):
        """Send initial threat data when user connects."""
        try:
            threats = await self.get_filtered_threats(1)  # Last 24 hours
            
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': threats,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending initial data: {str(e)}", exc_info=True)
    
    @database_sync_to_async
    def get_filtered_threats(self, days=1, threat_type='', severity=''):
        """Get filtered threat data from database."""
        try:
            since = timezone.now() - timedelta(days=days)
            
            # Get user's threats or all if staff
            if self.scope["user"].is_staff:
                queryset = ThreatEvent.objects.filter(timestamp__gte=since)
            else:
                queryset = ThreatEvent.objects.filter(
                    user=self.scope["user"],
                    timestamp__gte=since
                )
            
            # Apply filters
            if threat_type:
                queryset = queryset.filter(threat_type=threat_type)
            if severity:
                queryset = queryset.filter(severity=severity)
            
            # Only get threats with location data
            queryset = queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).order_by('-timestamp')[:1000]  # Limit to 1000 most recent
            
            # Serialize data
            serializer = ThreatEventSerializer(queryset, many=True)
            return serializer.data
            
        except Exception as e:
            logger.error(f"Error getting filtered threats: {str(e)}", exc_info=True)
            return []
    
    # Group message handlers
    async def threat_update(self, event):
        """Handle threat update messages from group."""
        try:
            threat_data = event['threat_data']
            
            # Check if this threat matches user's filters (if any)
            if hasattr(self, 'filters') and self.filters:
                if not self.matches_filters(threat_data, self.filters):
                    return
            
            await self.send(text_data=json.dumps({
                'type': 'threat_update',
                'data': threat_data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling threat update: {str(e)}", exc_info=True)
    
    async def threat_alert(self, event):
        """Handle critical threat alerts."""
        try:
            alert_data = event['alert_data']
            
            await self.send(text_data=json.dumps({
                'type': 'threat_alert',
                'data': alert_data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling threat alert: {str(e)}", exc_info=True)
    
    def matches_filters(self, threat_data, filters):
        """Check if threat data matches user's filters."""
        try:
            if filters.get('threat_type') and threat_data.get('threat_type') != filters['threat_type']:
                return False
            if filters.get('severity') and threat_data.get('severity') != filters['severity']:
                return False
            if filters.get('country') and threat_data.get('country') != filters['country']:
                return False
            return True
        except Exception:
            return True  # Default to showing if filter check fails


class GlobalThreatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for global threat statistics."""
    
    async def connect(self):
        """Handle WebSocket connection for global stats."""
        try:
            # Check if user is authenticated and is staff
            if self.scope["user"] == AnonymousUser() or not self.scope["user"].is_staff:
                logger.warning("Unauthorized user attempted to connect to global threat WebSocket")
                await self.close()
                return
            
            # Join global threat stats group
            self.group_name = "global_threat_stats"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"Staff user {self.scope['user'].id} connected to global threat WebSocket")
            
        except Exception as e:
            logger.error(f"Error in global threat WebSocket connect: {str(e)}", exc_info=True)
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            logger.info(f"User disconnected from global threat WebSocket with code: {close_code}")
        except Exception as e:
            logger.error(f"Error in global threat WebSocket disconnect: {str(e)}", exc_info=True)
    
    async def global_stats_update(self, event):
        """Handle global statistics updates."""
        try:
            stats_data = event['stats_data']
            
            await self.send(text_data=json.dumps({
                'type': 'global_stats_update',
                'data': stats_data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling global stats update: {str(e)}", exc_info=True)