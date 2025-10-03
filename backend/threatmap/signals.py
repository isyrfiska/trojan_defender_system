from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .tasks import send_threat_update
from .models import ThreatEvent, GlobalThreatStats


@receiver(post_save, sender=ThreatEvent)
def update_global_threat_stats(sender, instance, created, **kwargs):
    """Update global threat statistics when a new threat event is created."""
    if created:
        # Get or create stats for today
        today = timezone.now().date()
        stats, created = GlobalThreatStats.objects.get_or_create(date=today)
        
        # Update total threats
        stats.total_threats += 1
        
        # Update threat type counts
        if instance.threat_type == ThreatEvent.ThreatType.MALWARE:
            stats.malware_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.VIRUS:
            stats.virus_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.RANSOMWARE:
            stats.ransomware_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.TROJAN:
            stats.trojan_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.SPYWARE:
            stats.spyware_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.ADWARE:
            stats.adware_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.WORM:
            stats.worm_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.ROOTKIT:
            stats.rootkit_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.BACKDOOR:
            stats.backdoor_count += 1
        elif instance.threat_type == ThreatEvent.ThreatType.EXPLOIT:
            stats.exploit_count += 1
        else:  # OTHER
            stats.other_count += 1
        
        # Update severity counts
        if instance.severity == ThreatEvent.ThreatSeverity.LOW:
            stats.low_severity_count += 1
        elif instance.severity == ThreatEvent.ThreatSeverity.MEDIUM:
            stats.medium_severity_count += 1
        elif instance.severity == ThreatEvent.ThreatSeverity.HIGH:
            stats.high_severity_count += 1
        elif instance.severity == ThreatEvent.ThreatSeverity.CRITICAL:
            stats.critical_severity_count += 1
        
        # Update country distribution
        if instance.country:
            country_distribution = stats.country_distribution
            country_distribution[instance.country] = country_distribution.get(instance.country, 0) + 1
            stats.country_distribution = country_distribution
        
        # Save the updated stats
        stats.save()

        # Broadcast real-time update to the user's threat map channel
        try:
            if instance.user_id:
                send_threat_update(instance)
        except Exception:
            # Avoid breaking signal flow on broadcast errors
            pass