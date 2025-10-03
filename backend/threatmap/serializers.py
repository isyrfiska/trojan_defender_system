from rest_framework import serializers
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.html import strip_tags
import re
import logging
from .models import ThreatEvent, GlobalThreatStats

logger = logging.getLogger('api')


class ThreatEventSerializer(serializers.ModelSerializer):
    """Serializer for threat events."""
    
    threat_type_display = serializers.CharField(source='get_threat_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ThreatEvent
        fields = ['id', 'user', 'user_email', 'scan_result', 'threat_type', 'threat_type_display', 
                  'severity', 'severity_display', 'timestamp', 'ip_address', 'country', 'city', 
                  'latitude', 'longitude', 'description', 'file_name', 'file_hash']
        read_only_fields = ['id', 'user', 'timestamp']
        ref_name = 'ThreatMap_ThreatEvent'
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        if value:
            # Sanitize HTML and limit length
            sanitized = strip_tags(value).strip()[:1000]
            return sanitized
        return value
    
    def validate_file_name(self, value):
        """Validate and sanitize file name."""
        if value:
            # Sanitize filename - remove dangerous characters
            sanitized = re.sub(r'[^\w\-_\.]', '_', value)[:255]
            return sanitized
        return value
    
    def validate_file_hash(self, value):
        """Validate file hash format."""
        if value:
            # Check if it's a valid SHA-256 hash (64 hex characters)
            if not re.match(r'^[a-fA-F0-9]{64}$', value):
                raise serializers.ValidationError("Invalid SHA-256 hash format.")
            return value.lower()  # Normalize to lowercase
        return value
    
    def validate_country(self, value):
        """Validate and sanitize country name."""
        if value:
            # Sanitize and limit length
            sanitized = strip_tags(value).strip()[:100]
            return sanitized
        return value
    
    def validate_city(self, value):
        """Validate and sanitize city name."""
        if value:
            # Sanitize and limit length
            sanitized = strip_tags(value).strip()[:100]
            return sanitized
        return value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range."""
        if value is not None:
            if value < -90 or value > 90:
                raise serializers.ValidationError("Latitude must be between -90 and 90 degrees.")
            return round(value, 6)  # Round to 6 decimal places for precision
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range."""
        if value is not None:
            if value < -180 or value > 180:
                raise serializers.ValidationError("Longitude must be between -180 and 180 degrees.")
            return round(value, 6)  # Round to 6 decimal places for precision
        return value


class ThreatEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating threat events with enhanced validation."""
    
    # Add validators for fields
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    latitude = serializers.FloatField(
        required=False, 
        allow_null=True,
        validators=[
            MinValueValidator(-90, message="Latitude must be at least -90 degrees."),
            MaxValueValidator(90, message="Latitude must be at most 90 degrees.")
        ]
    )
    longitude = serializers.FloatField(
        required=False, 
        allow_null=True,
        validators=[
            MinValueValidator(-180, message="Longitude must be at least -180 degrees."),
            MaxValueValidator(180, message="Longitude must be at most 180 degrees.")
        ]
    )
    file_hash = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=64,
        validators=[
            RegexValidator(
                regex=r'^[a-fA-F0-9]{64}$',
                message="File hash must be a valid SHA-256 hash (64 hexadecimal characters)."
            )
        ]
    )
    
    class Meta:
        model = ThreatEvent
        fields = ['scan_result', 'threat_type', 'severity', 'ip_address', 'country', 'city', 
                  'latitude', 'longitude', 'description', 'file_name', 'file_hash']
        ref_name = 'ThreatMap_ThreatEventCreate'
    
    def validate_threat_type(self, value):
        """Validate threat type is one of the allowed choices."""
        valid_types = [choice[0] for choice in ThreatEvent.ThreatType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid threat type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_severity(self, value):
        """Validate severity is one of the allowed choices."""
        valid_severities = [choice[0] for choice in ThreatEvent.ThreatSeverity.choices]
        if value not in valid_severities:
            raise serializers.ValidationError(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")
        return value
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        if value:
            # Sanitize HTML and limit length
            sanitized = strip_tags(value).strip()[:1000]
            return sanitized
        return value
    
    def validate_file_name(self, value):
        """Validate and sanitize file name."""
        if value:
            # Check for dangerous patterns
            dangerous_patterns = [
                r'\.\./',  # Directory traversal
                r'^\./',   # Hidden files
                r'[<>:"|?*]',  # Windows invalid characters
                r'[\x00-\x1f]',  # Control characters
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, value):
                    raise serializers.ValidationError("Filename contains invalid characters.")
            
            # Sanitize filename - remove dangerous characters
            sanitized = re.sub(r'[^\w\-_\.]', '_', value)[:255]
            return sanitized
        return value
    
    def validate_country(self, value):
        """Validate and sanitize country name."""
        if value:
            # Sanitize and limit length
            sanitized = strip_tags(value).strip()[:100]
            if not sanitized:
                return ""
            return sanitized
        return value
    
    def validate_city(self, value):
        """Validate and sanitize city name."""
        if value:
            # Sanitize and limit length
            sanitized = strip_tags(value).strip()[:100]
            if not sanitized:
                return ""
            return sanitized
        return value
    
    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        logger.info(f"Creating threat event: {validated_data.get('threat_type')} by user {self.context['request'].user.id}")
        return super().create(validated_data)


class GlobalThreatStatsSerializer(serializers.ModelSerializer):
    """Serializer for global threat statistics."""
    
    class Meta:
        model = GlobalThreatStats
        fields = '__all__'
        ref_name = 'ThreatMap_GlobalThreatStats'


class ThreatMapDataSerializer(serializers.Serializer):
    """Serializer for threat map data with enhanced validation."""
    
    time_range = serializers.CharField(required=False, default='24h')
    country_filter = serializers.CharField(required=False, allow_blank=True)
    threat_type = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        ref_name = 'ThreatMap_ThreatMapData'
    
    def validate_time_range(self, value):
        """Validate time range is one of the allowed values."""
        valid_ranges = ['1h', '6h', '12h', '24h', '7d', '30d', 'all']
        if value not in valid_ranges:
            raise serializers.ValidationError(f"Invalid time range. Must be one of: {', '.join(valid_ranges)}")
        return value
    
    def validate_threat_type(self, value):
        """Validate threat type if provided."""
        if value:
            valid_types = [choice[0] for choice in ThreatEvent.ThreatType.choices]
            if value not in valid_types:
                raise serializers.ValidationError(f"Invalid threat type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_severity(self, value):
        """Validate severity if provided."""
        if value:
            valid_severities = [choice[0] for choice in ThreatEvent.ThreatSeverity.choices]
            if value not in valid_severities:
                raise serializers.ValidationError(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")
        return value
    
    def validate_country_filter(self, value):
        """Validate and sanitize country filter."""
        if value:
            # Sanitize HTML and limit length
            sanitized = strip_tags(value).strip()[:100]
            return sanitized
        return value