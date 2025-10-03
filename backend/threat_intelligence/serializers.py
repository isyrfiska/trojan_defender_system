from rest_framework import serializers
from .models import ThreatIntelligence, ThreatEvent, ThreatStatistics


class ThreatIntelligenceSerializer(serializers.ModelSerializer):
    """Serializer for ThreatIntelligence model"""
    
    class Meta:
        model = ThreatIntelligence
        fields = [
            'id', 'ip_address', 'country_code', 'country_name',
            'is_malicious', 'confidence_percentage', 'abuse_confidence',
            'usage_type', 'isp', 'domain', 'threat_types',
            'last_reported_at', 'created_at', 'updated_at', 'source_api'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        ref_name = 'TI_ThreatIntelligence'


class ThreatEventSerializer(serializers.ModelSerializer):
    """Serializer for ThreatEvent model"""
    
    threat_intelligence = ThreatIntelligenceSerializer(read_only=True)
    
    class Meta:
        model = ThreatEvent
        fields = [
            'id', 'threat_intelligence', 'event_type', 'severity',
            'latitude', 'longitude', 'description', 'raw_data',
            'detected_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        ref_name = 'TI_ThreatEvent'


class ThreatEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ThreatEvent instances"""
    
    class Meta:
        model = ThreatEvent
        fields = [
            'threat_intelligence', 'event_type', 'severity',
            'latitude', 'longitude', 'description', 'raw_data',
            'detected_at'
        ]
        ref_name = 'TI_ThreatEventCreate'


class ThreatStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for ThreatStatistics model"""
    
    class Meta:
        model = ThreatStatistics
        fields = [
            'id', 'date', 'total_threats', 'new_threats',
            'high_confidence_threats', 'top_countries',
            'threat_type_distribution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        ref_name = 'TI_ThreatStatistics'


class ThreatMapDataSerializer(serializers.Serializer):
    """Serializer for threat map visualization data"""
    
    ip_address = serializers.IPAddressField()
    country_code = serializers.CharField(max_length=2)
    country_name = serializers.CharField(max_length=100)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    threat_count = serializers.IntegerField()
    severity = serializers.CharField(max_length=20)
    last_seen = serializers.DateTimeField()

    class Meta:
        ref_name = 'TI_ThreatMapData'


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_threats = serializers.IntegerField()
    new_threats_today = serializers.IntegerField()
    high_confidence_threats = serializers.IntegerField()
    countries_affected = serializers.IntegerField()
    top_threat_types = serializers.DictField()
    threat_trend = serializers.ListField(child=serializers.DictField())

    class Meta:
        ref_name = 'TI_DashboardStats'