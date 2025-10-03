import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import ThreatIntelligence, ThreatEvent, ThreatStatistics
import json

logger = logging.getLogger(__name__)


class AbuseIPDBClient:
    """Client for AbuseIPDB API integration"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'ABUSEIPDB_API_KEY', None)
        self.base_url = 'https://api.abuseipdb.com/api/v2'
        self.headers = {
            'Key': self.api_key,
            'Accept': 'application/json',
        }
    
    def check_ip(self, ip_address, max_age_days=90):
        """Check a single IP address for abuse reports"""
        if not self.api_key:
            logger.error("AbuseIPDB API key not configured")
            return None
            
        url = f"{self.base_url}/check"
        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': max_age_days,
            'verbose': True
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking IP {ip_address}: {e}")
            return None
    
    def get_blacklist(self, confidence_minimum=75, limit=10000):
        """Get blacklisted IPs from AbuseIPDB"""
        if not self.api_key:
            logger.error("AbuseIPDB API key not configured")
            return None
            
        url = f"{self.base_url}/blacklist"
        params = {
            'confidenceMinimum': confidence_minimum,
            'limit': limit,
            'plaintext': False
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            # Check if response is JSON or plaintext
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                # Handle plaintext response - convert to expected JSON format
                ip_list = [ip.strip() for ip in response.text.strip().split('\n') if ip.strip()]
                return {
                    'data': [{'ipAddress': ip, 'abuseConfidencePercentage': confidence_minimum} for ip in ip_list]
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching blacklist: {e}")
            return None


class ThreatIntelligenceUpdater:
    """Service to update threat intelligence data from external APIs"""
    
    def __init__(self):
        self.abuseipdb = AbuseIPDBClient()
    
    def update_from_abuseipdb_blacklist(self, limit=10000, confidence_minimum=25):
        """Update threat intelligence from AbuseIPDB blacklist"""
        logger.info(f"Starting AbuseIPDB blacklist update (limit: {limit}, min confidence: {confidence_minimum})")
        
        blacklist_data = self.abuseipdb.get_blacklist(limit=limit, confidence_minimum=confidence_minimum)
        
        # Require API key - no fallback to mock data
        if not blacklist_data:
            logger.error("Failed to fetch data from AbuseIPDB API. Please ensure ABUSEIPDB_API_KEY is configured.")
            return False
        
        updated_count = 0
        created_count = 0
        
        for item in blacklist_data.get('data', []):
            try:
                ip_address = item.get('ipAddress')
                if not ip_address:
                    continue
                
                # Get or create ThreatIntelligence record
                threat_intel, created = ThreatIntelligence.objects.get_or_create(
                    ip_address=ip_address,
                    defaults={
                        'is_malicious': True,
                        'source_api': 'abuseipdb'
                    }
                )
                
                # Update fields
                threat_intel.country_code = item.get('countryCode')
                threat_intel.abuse_confidence = item.get('abuseConfidencePercentage', 0)
                threat_intel.usage_type = item.get('usageType')
                threat_intel.isp = item.get('isp')
                threat_intel.domain = item.get('domain')
                threat_intel.is_malicious = True
                threat_intel.confidence_percentage = item.get('abuseConfidencePercentage', 0)
                threat_intel.last_reported_at = timezone.now()
                threat_intel.save()
                
                if created:
                    created_count += 1
                    # Create a threat event for new threats
                    ThreatEvent.objects.create(
                        threat_intelligence=threat_intel,
                        event_type='blacklist_detection',
                        severity='high' if threat_intel.abuse_confidence > 90 else 'medium',
                        description=f"IP detected in AbuseIPDB blacklist with {threat_intel.abuse_confidence}% confidence"
                    )
                else:
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing IP {item.get('ipAddress', 'unknown')}: {e}")
                continue
        
        # Broadcast the statistics update
        from .signals import broadcast_threat_stats
        broadcast_threat_stats()
        
        logger.info(f"AbuseIPDB update complete: {created_count} created, {updated_count} updated")
        return True
    
    def check_specific_ips(self, ip_list):
        """Check specific IPs against AbuseIPDB"""
        results = []
        
        for ip in ip_list:
            try:
                data = self.abuseipdb.check_ip(ip)
                if not data:
                    continue
                
                ip_data = data.get('data', {})
                
                # Get or create ThreatIntelligence record
                threat_intel, created = ThreatIntelligence.objects.get_or_create(
                    ip_address=ip,
                    defaults={
                        'source_api': 'abuseipdb'
                    }
                )
                
                # Update fields
                threat_intel.country_code = ip_data.get('countryCode')
                threat_intel.country_name = ip_data.get('countryName')
                threat_intel.abuse_confidence = ip_data.get('abuseConfidencePercentage', 0)
                threat_intel.usage_type = ip_data.get('usageType')
                threat_intel.isp = ip_data.get('isp')
                threat_intel.domain = ip_data.get('domain')
                threat_intel.is_malicious = ip_data.get('abuseConfidencePercentage', 0) > 25
                threat_intel.confidence_percentage = ip_data.get('abuseConfidencePercentage', 0)
                threat_intel.last_reported_at = timezone.now()
                threat_intel.save()
                
                results.append(threat_intel)
                
                # Create threat event if malicious
                if threat_intel.is_malicious and created:
                    ThreatEvent.objects.create(
                        threat_intelligence=threat_intel,
                        event_type='ip_check',
                        severity='high' if threat_intel.abuse_confidence > 75 else 'medium',
                        description=f"Malicious IP detected with {threat_intel.abuse_confidence}% confidence"
                    )
                    
            except Exception as e:
                logger.error(f"Error checking IP {ip}: {e}")
                continue
        
        return results
    
    def update_daily_statistics(self):
        """Update daily threat statistics"""
        today = timezone.now().date()
        
        # Calculate statistics
        total_threats = ThreatIntelligence.objects.filter(is_malicious=True).count()
        new_threats = ThreatIntelligence.objects.filter(
            is_malicious=True,
            created_at__date=today
        ).count()
        high_confidence = ThreatIntelligence.objects.filter(
            is_malicious=True,
            abuse_confidence__gte=75
        ).count()
        
        # Top countries
        country_stats = {}
        threats_by_country = ThreatIntelligence.objects.filter(
            is_malicious=True,
            country_code__isnull=False
        ).values('country_code', 'country_name').distinct()
        
        for country in threats_by_country:
            count = ThreatIntelligence.objects.filter(
                is_malicious=True,
                country_code=country['country_code']
            ).count()
            country_stats[country['country_code']] = {
                'name': country['country_name'],
                'count': count
            }
        
        # Threat type distribution (simplified)
        threat_types = {
            'high_confidence': high_confidence,
            'medium_confidence': ThreatIntelligence.objects.filter(
                is_malicious=True,
                abuse_confidence__gte=25,
                abuse_confidence__lt=75
            ).count(),
            'low_confidence': ThreatIntelligence.objects.filter(
                is_malicious=True,
                abuse_confidence__lt=25
            ).count()
        }
        
        # Update or create statistics
        stats, created = ThreatStatistics.objects.get_or_create(
            date=today,
            defaults={
                'total_threats': total_threats,
                'new_threats': new_threats,
                'high_confidence_threats': high_confidence,
                'top_countries': country_stats,
                'threat_type_distribution': threat_types
            }
        )
        
        if not created:
            stats.total_threats = total_threats
            stats.new_threats = new_threats
            stats.high_confidence_threats = high_confidence
            stats.top_countries = country_stats
            stats.threat_type_distribution = threat_types
            stats.save()
        
        logger.info(f"Updated daily statistics for {today}")
        return stats