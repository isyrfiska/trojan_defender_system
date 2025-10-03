from django.contrib import admin
from .models import ThreatEvent, GlobalThreatStats


@admin.register(ThreatEvent)
class ThreatEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'threat_type', 'severity', 'user', 'country', 'city', 'timestamp']
    list_filter = ['threat_type', 'severity', 'timestamp', 'country']
    search_fields = ['description', 'file_name', 'file_hash', 'country', 'city']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(GlobalThreatStats)
class GlobalThreatStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_threats', 'malware_count', 'virus_count', 'ransomware_count', 'trojan_count']
    list_filter = ['date']
    readonly_fields = ['date', 'total_threats', 'malware_count', 'virus_count', 'ransomware_count', 
                      'trojan_count', 'spyware_count', 'adware_count', 'worm_count', 'rootkit_count', 
                      'backdoor_count', 'exploit_count', 'other_count', 'low_severity_count', 
                      'medium_severity_count', 'high_severity_count', 'critical_severity_count', 
                      'country_distribution']
    date_hierarchy = 'date'