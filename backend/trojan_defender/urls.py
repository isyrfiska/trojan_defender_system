from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.cache import cache_page
from .views import serve_react_app
from . import health_checks

# API documentation schema
schema_view = get_schema_view(
    openapi.Info(
        title="Trojan Defender API",
        default_version='v1',
        description="API for Trojan Defender security platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@trojandefender.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoints
    path('health/', health_checks.health_check, name='health_check'),
    path('health/detailed/', health_checks.detailed_health_check, name='detailed_health_check'),
    path('health/cache/', health_checks.cache_status, name='cache_status'),
    path('health/cache/clear/', health_checks.cache_clear, name='cache_clear'),
    path('health/ready/', health_checks.readiness_check, name='readiness_check'),
    path('health/live/', health_checks.liveness_check, name='liveness_check'),
    
    # API documentation - MUST come before catch-all patterns
    path('swagger<format>/', cache_page(60 * 15)(schema_view.without_ui(cache_timeout=0)), name='schema-json'),
    path('swagger/', cache_page(60 * 15)(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path('redoc/', cache_page(60 * 15)(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Root path for React app
    path('', serve_react_app, name='react-frontend'),
    
    # Catch-all pattern for React frontend routes (MUST be last)
    # Only match paths that don't start with api/, admin/, swagger, redoc, or assets
    re_path(r'^(?!api/|admin/|swagger|redoc|assets/).*$', serve_react_app, name='react-frontend-catchall'),
]

# Serve static files and frontend assets
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Serve frontend assets from Vite build
    from django.views.static import serve
    import os
    frontend_assets_root = os.path.join(settings.BASE_DIR, '..', 'frontend', 'dist', 'assets')
    urlpatterns += [
        re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': frontend_assets_root}),
    ]