import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import ThreatIntelligence, ThreatEvent, DailyThreatStats

User = get_user_model()


class ThreatIntelligenceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for threat intelligence real-time updates."""
    
    async def connect(self):
        # Add the channel to the threat intelligence group
        await self.channel_layer.group_add(
            'threat_intelligence',
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Send initial threat statistics
        await self.send_initial_stats()
    
    async def disconnect(self, close_code):
        # Remove the channel from the threat intelligence group
        await self.channel_layer.group_discard(
            'threat_intelligence',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'get_stats':
                await self.send_current_stats()
            elif message_type == 'get_recent_threats':
                limit = data.get('limit', 10)
                await self.send_recent_threats(limit)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def send_initial_stats(self):
        """Send initial threat statistics when client connects."""
        stats = await self.get_threat_stats()
        await self.send(text_data=json.dumps({
            'type': 'initial_stats',
            'data': stats
        }))
    
    async def send_current_stats(self):
        """Send current threat statistics."""
        stats = await self.get_threat_stats()
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'data': stats
        }))
    
    async def send_recent_threats(self, limit=10):
        """Send recent threat events."""
        threats = await self.get_recent_threats(limit)
        await self.send(text_data=json.dumps({
            'type': 'recent_threats',
            'data': threats
        }))
    
    # Message handlers for broadcasting updates
    async def threat_update(self, event):
        """Send threat intelligence updates."""
        await self.send(text_data=json.dumps({
            'type': 'threat_update',
            'data': event['data']
        }))
    
    async def stats_update(self, event):
        """Send statistics updates."""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'data': event['data']
        }))
    
    async def new_threat_event(self, event):
        """Send new threat event notifications."""
        await self.send(text_data=json.dumps({
            'type': 'new_threat_event',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_threat_stats(self):
        """Get current threat statistics."""
        try:
            # Get today's stats
            today = timezone.now().date()
            today_stats = DailyThreatStats.objects.filter(date=today).first()
            
            # Get total counts
            total_threats = ThreatIntelligence.objects.count()
            total_events = ThreatEvent.objects.count()
            
            # Get recent activity (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_events = ThreatEvent.objects.filter(
                created_at__gte=yesterday
            ).count()
            
            # Get threat severity distribution (based on ThreatEvent severity)
            from django.db.models import Count
            severity_counts_qs = ThreatEvent.objects.values('severity').annotate(count=Count('id'))
            severity_counts = {item['severity']: item['count'] for item in severity_counts_qs}
            # Ensure all keys exist
            for level in ['low', 'medium', 'high', 'critical']:
                severity_counts.setdefault(level, 0)
            
            return {
                'total_threats': total_threats,
                'total_events': total_events,
                'recent_events_24h': recent_events,
                'today_stats': {
                    'new_threats': today_stats.new_threats if today_stats else 0,
                    'updated_threats': today_stats.updated_threats if today_stats else 0,
                    'total_events': today_stats.total_events if today_stats else 0,
                } if today_stats else None,
                'severity_distribution': severity_counts,
                'last_updated': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'last_updated': timezone.now().isoformat()
            }
    
    @database_sync_to_async
    def get_recent_threats(self, limit=10):
        """Get recent threat events."""
        try:
            events = ThreatEvent.objects.select_related(
                'threat_intelligence'
            ).order_by('-created_at')[:limit]
            
            threat_list = []
            for event in events:
                ti = event.threat_intelligence
                threat_list.append({
                    'id': event.id,
                    'ip_address': ti.ip_address,
                    'country': ti.country_name or ti.country_code,
                    'threat_level': event.severity,
                    'event_type': event.event_type,
                    'description': event.description,
                    'created_at': event.created_at.isoformat(),
                    'confidence': ti.confidence_percentage
                })
            
            return threat_list
        except Exception as e:
            return []