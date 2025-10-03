from rest_framework import serializers
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils.html import strip_tags
import re
import os
import mimetypes
import logging
from .models import ScanResult, ScanThreat, YaraRule, ScanStatistics

logger = logging.getLogger('api')


class ScanThreatSerializer(serializers.ModelSerializer):
    """Serializer for scan threats."""
    
    threat_type_display = serializers.CharField(source='get_threat_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = ScanThreat
        fields = ['id', 'name', 'threat_type', 'threat_type_display', 'description', 
                  'location', 'detection_engine', 'detection_rule', 'severity', 'severity_display']
    
    def validate_name(self, value):
        """Validate and sanitize threat name."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Threat name cannot be empty.")
        
        # Sanitize HTML and limit length
        sanitized = strip_tags(value).strip()[:255]
        if not sanitized:
            raise serializers.ValidationError("Threat name contains only invalid characters.")
        
        return sanitized
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        if value:
            # Sanitize HTML and limit length
            sanitized = strip_tags(value).strip()[:1000]
            return sanitized
        return value
    
    def validate_location(self, value):
        """Validate file location path."""
        if value:
            # Basic path validation - no directory traversal
            if '..' in value or value.startswith('/'):
                raise serializers.ValidationError("Invalid file location path.")
            return value[:500]  # Limit length
        return value


class ScanResultSerializer(serializers.ModelSerializer):
    """Serializer for scan results."""
    
    threats = ScanThreatSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    threat_level_display = serializers.CharField(source='get_threat_level_display', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    threat_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanResult
        fields = ['id', 'user', 'user_email', 'file_name', 'file_size', 'file_type', 
                  'file_hash', 'upload_date', 'scan_date', 'status', 'status_display', 
                  'threat_level', 'threat_level_display', 'scan_duration', 'threats', 'threat_count']
        read_only_fields = ['id', 'user', 'file_hash', 'upload_date', 'scan_date', 
                           'status', 'threat_level', 'scan_duration']
    
    def get_threat_count(self, obj):
        return obj.threats.count()
    
    def validate_file_name(self, value):
        """Validate and sanitize file name."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("File name cannot be empty.")
        
        # Sanitize filename - remove dangerous characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', value)[:255]
        if not sanitized:
            raise serializers.ValidationError("File name contains only invalid characters.")
        
        return sanitized


class ScanResultListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing scan results."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    threat_level_display = serializers.CharField(source='get_threat_level_display', read_only=True)
    threat_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanResult
        fields = ['id', 'file_name', 'file_size', 'file_type', 'upload_date', 
                  'scan_date', 'status', 'status_display', 'threat_level', 
                  'threat_level_display', 'threat_count']
    
    def get_threat_count(self, obj):
        return obj.threats.count()


class FileUploadSerializer(serializers.Serializer):
    """Enhanced serializer for file uploads with comprehensive validation."""
    
    file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['exe', 'dll', 'pdf', 'doc', 'docx', 'zip', 'rar', 
                                  '7z', 'tar', 'gz', 'bin', 'iso', 'img', 'apk', 'jar'],
                message="File extension not allowed for scanning."
            )
        ]
    )
    
    def validate_file(self, value):
        """Comprehensive file validation."""
        from django.conf import settings
        
        # Log file upload attempt
        logger.info(f"File upload validation: {value.name} ({value.size} bytes)")
        
        # Check if file is empty
        if value.size == 0:
            raise serializers.ValidationError("Empty files are not allowed.")
        
        # Check file size limits
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 100 * 1024 * 1024)  # 100MB default
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size / (1024 * 1024):.1f} MB) exceeds the limit of {max_size / (1024 * 1024)} MB."
            )
        
        # Minimum file size check (avoid tiny malicious files)
        min_size = getattr(settings, 'MIN_UPLOAD_SIZE', 1)  # 1 byte minimum
        if value.size < min_size:
            raise serializers.ValidationError("File is too small to be valid.")
        
        # Validate filename
        if not value.name or len(value.name.strip()) == 0:
            raise serializers.ValidationError("File must have a valid name.")
        
        # Check for dangerous filename patterns
        dangerous_patterns = [
            r'\.\./',  # Directory traversal
            r'^\./',   # Hidden files
            r'[<>:"|?*]',  # Windows invalid characters
            r'[\x00-\x1f]',  # Control characters
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value.name):
                raise serializers.ValidationError("Filename contains invalid characters.")
        
        # Sanitize filename
        original_name = value.name
        sanitized_name = re.sub(r'[^\w\-_\.]', '_', value.name)
        
        # Ensure filename isn't too long
        if len(sanitized_name) > 255:
            name_part, ext_part = os.path.splitext(sanitized_name)
            sanitized_name = name_part[:250] + ext_part
        
        if sanitized_name != original_name:
            logger.info(f"Filename sanitized: '{original_name}' -> '{sanitized_name}'")
            value.name = sanitized_name
        
        # MIME type validation
        mime_type, _ = mimetypes.guess_type(value.name)
        if mime_type:
            # Log potentially dangerous MIME types
            dangerous_mime_types = [
                'application/x-msdownload',
                'application/x-executable',
                'application/x-msdos-program',
                'text/x-shellscript',
                'application/x-sh',
                'application/javascript',
                'text/javascript'
            ]
            
            if mime_type in dangerous_mime_types:
                logger.warning(
                    f"Potentially dangerous file uploaded: {value.name} (MIME: {mime_type})",
                    extra={'security': True}
                )
        
        # Read first chunk to check for suspicious content
        try:
            first_chunk = value.read(1024)
            
            # Check for null bytes (potential binary corruption or attack)
            if b'\x00' in first_chunk:
                logger.warning(f"File contains null bytes: {value.name}", extra={'security': True})
            
            # Check for script injection attempts in text files
            if mime_type and mime_type.startswith('text/'):
                suspicious_patterns = [
                    b'<script',
                    b'javascript:',
                    b'vbscript:',
                    b'onload=',
                    b'onerror=',
                ]
                
                for pattern in suspicious_patterns:
                    if pattern in first_chunk.lower():
                        logger.warning(
                            f"Suspicious script content detected in file: {value.name}",
                            extra={'security': True}
                        )
                        break
            
            # Reset file pointer
            value.seek(0)
            
        except Exception as e:
            logger.error(f"Error reading file during validation: {str(e)}")
            raise serializers.ValidationError("Unable to read file for validation.")
        
        return value


class YaraRuleSerializer(serializers.ModelSerializer):
    """Serializer for YARA rules with enhanced validation."""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    # Add validators for name field
    name = serializers.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_\-\s]+$',
                message="Rule name can only contain letters, numbers, spaces, hyphens, and underscores."
            )
        ]
    )
    
    class Meta:
        model = YaraRule
        fields = ['id', 'name', 'description', 'rule_content', 'is_active', 
                  'created_by', 'created_by_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate and sanitize rule name."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Rule name cannot be empty.")
        
        # Sanitize and validate
        sanitized = strip_tags(value).strip()
        if len(sanitized) < 3:
            raise serializers.ValidationError("Rule name must be at least 3 characters long.")
        
        if len(sanitized) > 100:
            raise serializers.ValidationError("Rule name cannot exceed 100 characters.")
        
        return sanitized
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        if value:
            # Sanitize HTML and limit length
            sanitized = strip_tags(value).strip()
            if len(sanitized) > 500:
                raise serializers.ValidationError("Description cannot exceed 500 characters.")
            return sanitized
        return value
    
    def validate_rule_content(self, value):
        """Comprehensive YARA rule validation."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Rule content cannot be empty.")
        
        # Basic YARA syntax validation
        required_elements = ['rule ', '{', '}']
        for element in required_elements:
            if element not in value:
                raise serializers.ValidationError(f"Invalid YARA rule syntax: missing '{element}'.")
        
        # Check for potentially dangerous operations
        dangerous_patterns = [
            'import "pe"',  # PE module can be resource intensive
            'import "elf"',  # ELF module can be resource intensive
            'for all',  # Potentially expensive loops
            'for any',  # Potentially expensive loops
        ]
        
        for pattern in dangerous_patterns:
            if pattern in value.lower():
                logger.warning(
                    f"YARA rule contains potentially expensive operation: {pattern}",
                    extra={'security': True}
                )
        
        # Validate rule length
        if len(value) > 10000:  # 10KB limit
            raise serializers.ValidationError("YARA rule content is too large (max 10KB).")
        
        # Basic rule name extraction and validation
        try:
            rule_match = re.search(r'rule\s+(\w+)', value)
            if not rule_match:
                raise serializers.ValidationError("Could not extract rule name from content.")
            
            rule_name = rule_match.group(1)
            if len(rule_name) > 50:
                raise serializers.ValidationError("Rule name in content is too long (max 50 characters).")
                
        except Exception as e:
            logger.error(f"Error parsing YARA rule: {str(e)}")
            raise serializers.ValidationError("Invalid YARA rule format.")
        
        return value
    
    def create(self, validated_data):
        """Create YARA rule with user assignment."""
        validated_data['created_by'] = self.context['request'].user
        logger.info(f"Creating YARA rule: {validated_data['name']} by user {self.context['request'].user.id}")
        return super().create(validated_data)


class ScanStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for scan statistics."""
    
    class Meta:
        model = ScanStatistics
        fields = '__all__'
        read_only_fields = ['id', 'date', 'total_scans', 'clean_files', 'infected_files', 
                           'total_threats', 'avg_scan_time']