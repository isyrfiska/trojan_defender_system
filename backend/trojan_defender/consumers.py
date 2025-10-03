import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

class GeneralWebSocketConsumer(AsyncWebsocketConsumer):
    """General WebSocket consumer for main application connections."""
    
    async def connect(self):
        # Get JWT token from query parameters
        token = self.scope['query_string'].decode().split('token=')[-1] if 'token=' in self.scope['query_string'].decode() else None
        
        if token:
            try:
                # Validate JWT token
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth import get_user_model
                
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                User = get_user_model()
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                
                self.scope['user'] = user
                await self.accept()
                
                # Join user-specific group
                await self.channel_layer.group_add(
                    f"user_{user.id}",
                    self.channel_name
                )
                
            except Exception as e:
                await self.close()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self.scope, 'user') and self.scope['user'].is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{self.scope['user'].id}",
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'subscribe':
                # Handle subscription to specific channels
                channel = data.get('channel')
                if channel in ['scan_updates', 'threat_updates', 'system_notifications']:
                    await self.channel_layer.group_add(
                        channel,
                        self.channel_name
                    )
                    await self.send(text_data=json.dumps({
                        'type': 'subscription_confirmed',
                        'channel': channel
                    }))
            
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
    
    # Message handlers for different types of updates
    async def send_scan_update(self, event):
        """Send scan status updates."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def send_threat_update(self, event):
        """Send threat detection updates."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def send_system_notification(self, event):
        """Send system notifications."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def send_user_notification(self, event):
        """Send user-specific notifications."""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token."""
        try:
            # Validate the token
            UntypedToken(token)
            
            # Decode the token to get user info
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get the user
            user = User.objects.get(id=user_id)
            return user
            
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()