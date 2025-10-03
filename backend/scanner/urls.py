from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScanResultViewSet, FileUploadView, YaraRuleViewSet, ScanStatisticsViewSet
)

router = DefaultRouter()
router.register(r'results', ScanResultViewSet, basename='scan-result')
router.register(r'scans', ScanResultViewSet, basename='scan')  # Alias to satisfy tests expecting /api/scanner/scans/
router.register(r'upload', FileUploadView, basename='file-upload')
router.register(r'yara-rules', YaraRuleViewSet, basename='yara-rule')
router.register(r'statistics', ScanStatisticsViewSet, basename='scan-statistics')

urlpatterns = [
    path('', include(router.urls)),
    # Add custom endpoint for stats that frontend expects
    path('stats/', ScanStatisticsViewSet.as_view({'get': 'summary'}), name='scan-stats'),
]