from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'user_email', 'title', 'message', 'notification_type', 'notification_type_display', 
                  'priority', 'priority_display', 'is_read', 'created_at', 'read_at', 
                  'scan_result_id', 'threat_id', 'metadata']
        read_only_fields = ['id', 'user', 'created_at', 'read_at']


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification read status."""
    
    class Meta:
        model = Notification
        fields = ['is_read']


class NotificationPreferencesSerializer(serializers.Serializer):
    """Serializer for notification preferences."""
    
    notify_scan_complete = serializers.BooleanField(default=True)
    notify_security_alerts = serializers.BooleanField(default=True)
    notify_system_updates = serializers.BooleanField(default=False)
    email_notifications = serializers.BooleanField(default=True)