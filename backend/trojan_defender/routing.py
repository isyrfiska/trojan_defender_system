from django.urls import re_path
from scanner.consumers import UnifiedScanConsumer
from threatmap.consumers import ThreatMapConsumer
from threat_intelligence.consumers import ThreatIntelligenceConsumer
from .consumers import GeneralWebSocketConsumer

websocket_urlpatterns = [
    re_path(r'ws/$', GeneralWebSocketConsumer.as_asgi()),
    re_path(r'ws/scan-status/$', UnifiedScanConsumer.as_asgi()),
    re_path(r'ws/threat-map/$', ThreatMapConsumer.as_asgi()),
    re_path(r'ws/threat-intelligence/$', ThreatIntelligenceConsumer.as_asgi()),
]