import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ThreatEvent(models.Model):
    """Model to store threat events for the threat map."""
    
    class ThreatType(models.TextChoices):
        MALWARE = 'malware', _('Malware')
        VIRUS = 'virus', _('Virus')
        RANSOMWARE = 'ransomware', _('Ransomware')
        TROJAN = 'trojan', _('Trojan')
        SPYWARE = 'spyware', _('Spyware')
        ADWARE = 'adware', _('Adware')
        WORM = 'worm', _('Worm')
        ROOTKIT = 'rootkit', _('Rootkit')
        BACKDOOR = 'backdoor', _('Backdoor')
        EXPLOIT = 'exploit', _('Exploit')
        OTHER = 'other', _('Other')
    
    class ThreatSeverity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='threat_events')
    scan_result = models.ForeignKey('scanner.ScanResult', on_delete=models.SET_NULL, null=True, related_name='threat_events')
    threat_type = models.CharField(max_length=20, choices=ThreatType.choices)
    severity = models.CharField(max_length=20, choices=ThreatSeverity.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Location information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Additional information
    description = models.TextField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_hash = models.CharField(max_length=64, blank=True)  # SHA-256 hash
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_threat_type_display()} - {self.timestamp}"


class GlobalThreatStats(models.Model):
    """Model to store global threat statistics."""
    
    date = models.DateField(unique=True)
    total_threats = models.IntegerField(default=0)
    malware_count = models.IntegerField(default=0)
    virus_count = models.IntegerField(default=0)
    ransomware_count = models.IntegerField(default=0)
    trojan_count = models.IntegerField(default=0)
    spyware_count = models.IntegerField(default=0)
    adware_count = models.IntegerField(default=0)
    worm_count = models.IntegerField(default=0)
    rootkit_count = models.IntegerField(default=0)
    backdoor_count = models.IntegerField(default=0)
    exploit_count = models.IntegerField(default=0)
    other_count = models.IntegerField(default=0)
    
    # Severity counts
    low_severity_count = models.IntegerField(default=0)
    medium_severity_count = models.IntegerField(default=0)
    high_severity_count = models.IntegerField(default=0)
    critical_severity_count = models.IntegerField(default=0)
    
    # Geographic distribution (JSON field)
    country_distribution = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Global Threat Statistics'
        verbose_name_plural = 'Global Threat Statistics'
    
    def __str__(self):
        return f"Threat Stats for {self.date}"
