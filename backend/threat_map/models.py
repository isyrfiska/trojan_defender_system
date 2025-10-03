import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class ThreatSource(models.Model):
    """Model to store threat intelligence sources."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ThreatData(models.Model):
    """Model to store threat intelligence data."""
    
    class ThreatType(models.TextChoices):
        MALWARE = 'malware', _('Malware')
        PHISHING = 'phishing', _('Phishing')
        BOTNET = 'botnet', _('Botnet')
        SPAM = 'spam', _('Spam')
        EXPLOIT = 'exploit', _('Exploit')
        RANSOMWARE = 'ransomware', _('Ransomware')
        OTHER = 'other', _('Other')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(ThreatSource, on_delete=models.CASCADE, related_name='threat_data')
    threat_type = models.CharField(max_length=50, choices=ThreatType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    hash_value = models.CharField(max_length=64, blank=True)  # SHA-256 hash
    country = models.CharField(max_length=2, blank=True)  # ISO country code
    description = models.TextField(blank=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    confidence = models.IntegerField(default=50)  # 0-100 confidence score
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['domain']),
            models.Index(fields=['hash_value']),
            models.Index(fields=['country']),
            models.Index(fields=['threat_type']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        if self.ip_address:
            return f"{self.ip_address} ({self.threat_type})"
        elif self.domain:
            return f"{self.domain} ({self.threat_type})"
        elif self.hash_value:
            return f"{self.hash_value[:8]}... ({self.threat_type})"
        else:
            return f"Threat {self.id} ({self.threat_type})"