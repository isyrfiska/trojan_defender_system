from django.urls import path
from .views import (RegisterView, UserProfileView, PasswordChangeView,
                   NotificationPreferencesView, NotificationActionsView, TestEmailView)
from .auth_views import CustomTokenObtainPairView, AlternativeTokenObtainPairView, CustomTokenRefreshView
from .enhanced_auth_views import EnhancedTokenRefreshView, TokenStatusView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('user/', UserProfileView.as_view(), name='user'),  # Alias to satisfy tests expecting /api/auth/user/
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', AlternativeTokenObtainPairView.as_view(), name='token_obtain_pair_alt'),
    path('token/refresh/', EnhancedTokenRefreshView.as_view(), name='token_refresh'),
    path('token/status/', TokenStatusView.as_view(), name='token_status'),
    
    # User-specific notification endpoints (preferences and actions only)
    path('notifications/preferences/', NotificationPreferencesView.as_view(), name='notification-preferences'),
    path('notifications/actions/', NotificationActionsView.as_view(), name='notification-actions'),
    path('test-email/', TestEmailView.as_view(), name='test-email'),
]