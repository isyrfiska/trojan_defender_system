from django.db import models
from django.utils import timezone


class ThreatIntelligence(models.Model):
    """Model to store threat intelligence data from external APIs"""
    
    # IP Address information
    ip_address = models.GenericIPAddressField(unique=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    
    # Threat information
    is_malicious = models.BooleanField(default=False)
    confidence_percentage = models.IntegerField(default=0)
    abuse_confidence = models.IntegerField(default=0)
    
    # Usage and reporting stats
    usage_type = models.CharField(max_length=50, null=True, blank=True)
    isp = models.CharField(max_length=200, null=True, blank=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    
    # Threat categories
    threat_types = models.JSONField(default=list, blank=True)
    
    # Timestamps
    last_reported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # API source information
    source_api = models.CharField(max_length=50, default='abuseipdb')
    
    class Meta:
        db_table = 'threat_intelligence'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.ip_address} - Malicious: {self.is_malicious}"


class ThreatEvent(models.Model):
    """Model to store real-time threat events"""
    
    threat_intelligence = models.ForeignKey(
        ThreatIntelligence, 
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    # Event details
    event_type = models.CharField(max_length=50)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    
    # Geographic information
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Additional metadata
    description = models.TextField(blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'threat_events'
        ordering = ['-detected_at']
        
    def __str__(self):
        return f"{self.event_type} - {self.threat_intelligence.ip_address}"


class ThreatStatistics(models.Model):
    """Model to store aggregated threat statistics"""
    
    # Time period
    date = models.DateField(unique=True)
    
    # Counts
    total_threats = models.IntegerField(default=0)
    new_threats = models.IntegerField(default=0)
    high_confidence_threats = models.IntegerField(default=0)
    
    # Geographic distribution
    top_countries = models.JSONField(default=dict, blank=True)
    
    # Threat type distribution
    threat_type_distribution = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'threat_statistics'
        ordering = ['-date']
        
    def __str__(self):
        return f"Stats for {self.date} - {self.total_threats} threats"


# Alias for backward compatibility
DailyThreatStats = ThreatStatistics
