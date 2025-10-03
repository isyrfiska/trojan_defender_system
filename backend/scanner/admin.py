from django.contrib import admin
from .models import ScanResult, ScanThreat, YaraRule, ScanStatistics


class ScanThreatInline(admin.TabularInline):
    model = ScanThreat
    extra = 0
    readonly_fields = ['name', 'threat_type', 'description', 'location', 'detection_engine', 'detection_rule', 'severity']
    can_delete = False


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'file_name', 'user', 'upload_date', 'scan_date', 'status', 'threat_level', 'scan_duration']
    list_filter = ['status', 'threat_level', 'upload_date', 'scan_date']
    search_fields = ['file_name', 'file_hash', 'user__email']
    readonly_fields = ['id', 'user', 'file_name', 'file_size', 'file_type', 'file_hash', 'upload_date', 'scan_date', 'scan_duration', 'storage_path']
    inlines = [ScanThreatInline]
    date_hierarchy = 'upload_date'


@admin.register(ScanThreat)
class ScanThreatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'threat_type', 'severity', 'detection_engine', 'scan_result']
    list_filter = ['threat_type', 'severity', 'detection_engine']
    search_fields = ['name', 'description', 'detection_rule']
    readonly_fields = ['scan_result']


@admin.register(YaraRule)
class YaraRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'rule_content']
    readonly_fields = ['created_by', 'created_at', 'updated_at']


@admin.register(ScanStatistics)
class ScanStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_scans', 'clean_files', 'infected_files', 'total_threats']
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['date', 'total_scans', 'clean_files', 'infected_files', 'total_threats', 'avg_scan_duration']