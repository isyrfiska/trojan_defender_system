from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from notifications.models import Notification

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'organization', 
                  'job_title', 'phone_number', 'profile_picture', 'date_joined',
                  'notify_scan_complete', 'notify_security_alerts']
        read_only_fields = ['id', 'email', 'date_joined']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer for login endpoint"""
    pass


class AlternativeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Alternative serializer for token endpoint"""
    pass


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 
                  'organization', 'job_title', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications."""
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'priority', 
                  'is_read', 'created_at', 'read_at', 'scan_result_id', 
                  'threat_id', 'metadata']
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""
    
    class Meta:
        model = User
        fields = ['notify_scan_complete', 'notify_security_alerts']


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification status."""
    
    class Meta:
        model = Notification
        fields = ['is_read']
        
    def update(self, instance, validated_data):
        if validated_data.get('is_read') and not instance.is_read:
            instance.mark_as_read()
        return instance