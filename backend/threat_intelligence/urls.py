from django.urls import path
from . import views

app_name = 'threat_intelligence'

urlpatterns = [
    # List views
    path('threats/', views.ThreatIntelligenceListView.as_view(), name='threat-list'),
    path('events/', views.ThreatEventListView.as_view(), name='event-list'),
    
    # Dashboard and map data
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('map/data/', views.threat_map_data, name='threat-map-data'),
    
    # Statistics
    path('statistics/', views.threat_statistics, name='threat-statistics'),
    
    # Actions
    path('update/', views.update_threat_data, name='update-threat-data'),
    path('check-ips/', views.check_ips, name='check-ips'),
]