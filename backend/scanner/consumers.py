import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ScanResult


class UnifiedScanConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for unified scan status updates (file + network)."""
    
    async def connect(self):
        # Add the channel to the unified scan group
        await self.channel_layer.group_add(
            'unified_scan_status',
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        # Remove the channel from all groups
        await self.channel_layer.group_discard(
            'unified_scan_status',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            
            # Handle subscription to specific scan IDs
            if data.get('action') == 'subscribe':
                scan_id = data.get('scan_id')
                scan_type = data.get('scan_type', 'file')  # 'file' or 'network'
                
                if scan_id and await self.user_can_access_scan(scan_id, scan_type):
                    # Add to scan-specific group
                    await self.channel_layer.group_add(
                        f'{scan_type}_scan_{scan_id}',
                        self.channel_name
                    )
                    
                    # Send current status
                    current_status = await self.get_scan_status(scan_id, scan_type)
                    await self.send(text_data=json.dumps(current_status))
                else:
                    await self.send(text_data=json.dumps({
                        'error': 'Access denied or scan not found'
                    }))
                    
            # Handle real-time scan requests
            elif data.get('action') == 'start_realtime_scan':
                scan_config = data.get('config', {})
                await self.start_realtime_scan(scan_config)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def send_update(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def send_realtime_update(self, event):
        """Send real-time scan updates."""
        await self.send(text_data=json.dumps({
            'type': 'realtime_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def user_can_access_scan(self, scan_id, scan_type):
        """Check if the current user can access the scan."""
        user = self.scope.get('user')
        
        if user.is_anonymous:
            return False
        
        try:
            if scan_type == 'file':
                scan = ScanResult.objects.get(id=scan_id)
            else:  # network
                scan = NetworkScan.objects.get(id=scan_id)
            
            return scan.user == user or user.is_staff
        except (ScanResult.DoesNotExist, NetworkScan.DoesNotExist):
            return False
    
    @database_sync_to_async
    def get_scan_status(self, scan_id, scan_type):
        """Get the current status of a scan."""
        try:
            if scan_type == 'file':
                scan = ScanResult.objects.get(id=scan_id)
                return {
                    'scan_id': str(scan.id),
                    'scan_type': 'file',
                    'status': scan.status,
                    'status_display': scan.get_status_display(),
                    'threat_level': scan.threat_level,
                    'threat_level_display': scan.get_threat_level_display(),
                    'scan_date': scan.scan_date.isoformat() if scan.scan_date else None,
                    'scan_duration': scan.scan_duration,
                    'threat_count': scan.threats.count()
                }
            else:  # network
                scan = NetworkScan.objects.get(id=scan_id)
                return {
                    'scan_id': str(scan.id),
                    'scan_type': 'network',
                    'status': scan.status,
                    'total_packets': scan.total_packets,
                    'unique_ips': scan.unique_ips,
                    'suspicious_connections': scan.suspicious_connections,
                    'threat_score': scan.threat_score,
                    'ai_analysis_complete': scan.ai_analysis_complete,
                    'analysis_date': scan.analysis_date.isoformat() if scan.analysis_date else None,
                    'threat_count': scan.network_threats.count()
                }
        except (ScanResult.DoesNotExist, NetworkScan.DoesNotExist):
            return {'error': 'Scan not found'}
    
    async def start_realtime_scan(self, config):
        """Start real-time network monitoring."""
        # This would integrate with live network capture
        await self.send(text_data=json.dumps({
            'type': 'realtime_scan_started',
            'message': 'Real-time network monitoring started',
            'config': config
        }))