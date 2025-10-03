import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ScanResult(models.Model):
    """Model to store file scan results."""
    
    class ScanStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SCANNING = 'scanning', _('Scanning')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
    
    class ThreatLevel(models.TextChoices):
        CLEAN = 'clean', _('Clean')
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scan_results')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    file_hash = models.CharField(max_length=64)  # SHA-256 hash
    upload_date = models.DateTimeField(auto_now_add=True)
    scan_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ScanStatus.choices, default=ScanStatus.PENDING)
    threat_level = models.CharField(max_length=20, choices=ThreatLevel.choices, default=ThreatLevel.CLEAN)
    scan_duration = models.FloatField(null=True, blank=True)  # in seconds
    
    # Storage information
    storage_path = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.file_name} - {self.get_status_display()}"


class ScanThreat(models.Model):
    """Model to store detected threats in a scan."""
    
    class ThreatType(models.TextChoices):
        VIRUS = 'virus', _('Virus')
        MALWARE = 'malware', _('Malware')
        RANSOMWARE = 'ransomware', _('Ransomware')
        TROJAN = 'trojan', _('Trojan')
        SPYWARE = 'spyware', _('Spyware')
        ADWARE = 'adware', _('Adware')
        WORM = 'worm', _('Worm')
        ROOTKIT = 'rootkit', _('Rootkit')
        BACKDOOR = 'backdoor', _('Backdoor')
        EXPLOIT = 'exploit', _('Exploit')
        OTHER = 'other', _('Other')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan_result = models.ForeignKey(ScanResult, on_delete=models.CASCADE, related_name='threats')
    name = models.CharField(max_length=255)
    threat_type = models.CharField(max_length=20, choices=ThreatType.choices, default=ThreatType.OTHER)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # Path within archive or file offset
    detection_engine = models.CharField(max_length=50)  # ClamAV, YARA, etc.
    detection_rule = models.CharField(max_length=255, blank=True)  # Rule that triggered the detection
    severity = models.CharField(max_length=20, choices=ScanResult.ThreatLevel.choices)
    
    class Meta:
        ordering = ['-severity']
    
    def __str__(self):
        return f"{self.name} ({self.get_threat_type_display()})"


class YaraRule(models.Model):
    """Model to store custom YARA rules."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rule_content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='yara_rules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ScanStatistics(models.Model):
    """Model to store aggregated scan statistics."""
    
    date = models.DateField(unique=True)
    total_scans = models.IntegerField(default=0)
    clean_files = models.IntegerField(default=0)
    infected_files = models.IntegerField(default=0)
    total_threats = models.IntegerField(default=0)
    avg_scan_duration = models.FloatField(default=0.0)  # in seconds
    total_file_size = models.BigIntegerField(default=0)  # in bytes
    
    # Threat type distribution
    virus_count = models.IntegerField(default=0)
    malware_count = models.IntegerField(default=0)
    ransomware_count = models.IntegerField(default=0)
    trojan_count = models.IntegerField(default=0)
    spyware_count = models.IntegerField(default=0)
    adware_count = models.IntegerField(default=0)
    worm_count = models.IntegerField(default=0)
    rootkit_count = models.IntegerField(default=0)
    backdoor_count = models.IntegerField(default=0)
    exploit_count = models.IntegerField(default=0)
    other_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Scan Statistics for {self.date}"


# Aliases for backward compatibility with tests
Scan = ScanResult
Threat = ScanThreat

# Add filename property to ScanResult for test compatibility
def _get_filename(self):
    return self.file_name

def _set_filename(self, value):
    self.file_name = value

ScanResult.filename = property(_get_filename, _set_filename)

# Add created_at property to ScanResult for test compatibility  
def _get_created_at(self):
    return self.upload_date

ScanResult.created_at = property(_get_created_at)

# Add threat_name property to ScanThreat for test compatibility
def _get_threat_name(self):
    return self.name

def _set_threat_name(self, value):
    self.name = value

ScanThreat.threat_name = property(_get_threat_name, _set_threat_name)

# Add scan property to ScanThreat for test compatibility
def _get_scan(self):
    return self.scan_result

def _set_scan(self, value):
    self.scan_result = value

ScanThreat.scan = property(_get_scan, _set_scan)

# Add engine property to ScanThreat for test compatibility
def _get_engine(self):
    return self.detection_engine

def _set_engine(self, value):
    self.detection_engine = value

ScanThreat.engine = property(_get_engine, _set_engine)