from django.urls import path, include
from users.auth_views import CustomTokenObtainPairView
from .views import APIRoot

urlpatterns = [
    # API root
    path('', APIRoot.as_view(), name='api-root'),

    # Authentication endpoints
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Removed duplicate refresh route; rely on users.urls for token refresh
    path('auth/', include('users.urls')),
    
    # App endpoints
    path('scanner/', include('scanner.urls')),
    path('threatmap/', include('threatmap.urls')),
    path('notifications/', include('notifications.urls')),
    path('threat-intelligence/', include('threat_intelligence.urls')),
]