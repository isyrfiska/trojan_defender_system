from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ThreatEventViewSet, ThreatMapViewSet, GlobalThreatStatsViewSet

router = DefaultRouter()
router.register(r'events', ThreatEventViewSet, basename='threat-event')
router.register(r'map', ThreatMapViewSet, basename='threat-map')
router.register(r'stats', GlobalThreatStatsViewSet, basename='threat-stats')

urlpatterns = [
    path('', include(router.urls)),
]