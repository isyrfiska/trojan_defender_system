from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
import logging

from .serializers import (UserSerializer, UserRegistrationSerializer, PasswordChangeSerializer,
                         NotificationSerializer, NotificationPreferencesSerializer, 
                         NotificationUpdateSerializer)
from notifications.models import Notification
from trojan_defender.cache_utils import cache_user_data, default_cache, invalidate_user_cache

# Security logger
security_logger = logging.getLogger('django.security')

User = get_user_model()


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='post')
class RegisterView(generics.CreateAPIView):
    """API view for user registration."""
    
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        security_logger.info(f'Registration attempt from IP: {request.META.get("REMOTE_ADDR")}')
        return super().create(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating user profile."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve user profile with caching."""
        cache_key = f"user_profile:{request.user.id}"
        
        # Try to get from cache first
        cached_profile = default_cache.cache.get(cache_key)
        if cached_profile:
            return Response(cached_profile)
        
        # Get fresh data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache the response for 30 minutes
        default_cache.cache.set(cache_key, serializer.data, 1800)
        
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user profile and invalidate cache."""
        response = super().update(request, *args, **kwargs)
        
        # Invalidate user cache after update
        invalidate_user_cache(request.user.id)
        
        return response


@method_decorator(ratelimit(key='user', rate='3/m', method='POST', block=True), name='post')
class PasswordChangeView(APIView):
    """API view for changing password."""
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                security_logger.warning(f'Failed password change attempt for user: {user.email} from IP: {request.META.get("REMOTE_ADDR")}')
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            security_logger.info(f'Password changed successfully for user: {user.email}')
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationPreferencesView(APIView):
    """API view for managing notification preferences."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = NotificationPreferencesSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = NotificationPreferencesSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationActionsView(APIView):
    """API view for notification bulk actions."""
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return available actions and current unread count (for test healthcheck)."""
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({
            "available_actions": ["mark_all_read", "get_unread_count"],
            "unread_count": unread_count
        })
    
    def post(self, request):
        action = request.data.get('action')
        
        if action == 'mark_all_read':
            notifications = Notification.objects.filter(user=request.user, is_read=False)
            for notification in notifications:
                notification.mark_as_read()
            return Response({"message": f"Marked {notifications.count()} notifications as read"})
        
        elif action == 'get_unread_count':
            count = Notification.objects.filter(user=request.user, is_read=False).count()
            return Response({"count": count})
        
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='user', rate='1/m', method='POST', block=True), name='post')
class TestEmailView(APIView):
    """API view for testing email notifications."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            subject = 'Test Email - Trojan Defender'
            message = f'Hello {user.get_full_name()},\n\nThis is a test email from Trojan Defender to verify your email notification settings are working correctly.\n\nBest regards,\nTrojan Defender Team'
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Create notification record
            Notification.objects.create(
                user=user,
                title='Test Email Sent',
                message='A test email has been sent to verify your email settings.',
                notification_type=Notification.NotificationType.EMAIL_SENT,
                priority=Notification.Priority.LOW
            )
            
            return Response({"message": "Test email sent successfully"})
        
        except Exception as e:
            security_logger.error(f'Failed to send test email to {user.email}: {str(e)}')
            return Response({"error": "Failed to send test email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)