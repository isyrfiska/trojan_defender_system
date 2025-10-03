import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ScanResult, ScanThreat
from notifications.models import Notification

# Security logger
security_logger = logging.getLogger('django.security')

@receiver(post_save, sender=ScanResult)
def notify_scan_completion(sender, instance, created, **kwargs):
    """Send notifications when a scan is completed."""
    # Only send notification when scan is completed and not when it's created
    if not created and instance.status == ScanResult.ScanStatus.COMPLETED:
        # Send email notification if user has enabled it
        if instance.user.notify_security_alerts and instance.threat_level != ScanResult.ThreatLevel.CLEAN:
            send_threat_notification_email(instance)
        
        # Send WebSocket notification to threat map
        if instance.threat_level != ScanResult.ThreatLevel.CLEAN:
            send_threat_map_update(instance)


def send_threat_notification_email(scan_result):
    """Send email notification about detected threats."""
    try:
        subject = f'[Trojan Defender] Threats Detected in {scan_result.file_name}'
        
        # Prepare context for email template
        context = {
            'user': scan_result.user,
            'scan_result': scan_result,
            'threats': scan_result.threats.all(),
            'app_url': settings.APP_URL,
        }
        
        # Render email templates
        html_message = render_to_string('scanner/emails/threat_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[scan_result.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Create notification record
        threats_count = scan_result.threats.count()
        Notification.objects.create(
            user=scan_result.user,
            title=f'Security Alert: {threats_count} threat(s) detected',
            message=f'Threats detected in scan of {scan_result.file_name}. Please review the scan results.',
            notification_type=Notification.NotificationType.THREAT_DETECTED,
            priority=Notification.Priority.HIGH,
            scan_result_id=scan_result.id
        )
        
    except Exception as e:
        # Log the error but don't raise it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending threat notification email: {str(e)}")


def send_threat_map_update(scan_result):
    """Send threat information to the threat map via WebSocket."""
    try:
        # Get user's location (IP-based or from profile)
        # This is a simplified example - in production, you'd use a proper geolocation service
        location = {
            'latitude': 0,  # Placeholder
            'longitude': 0,  # Placeholder
            'country': 'Unknown',
            'city': 'Unknown',
        }
        
        # Prepare threat data
        threat_data = {
            'scan_id': str(scan_result.id),
            'user_id': str(scan_result.user.id),
            'file_name': scan_result.file_name,
            'threat_level': scan_result.threat_level,
            'threat_count': scan_result.threats.count(),
            'location': location,
            'timestamp': scan_result.scan_date.isoformat() if scan_result.scan_date else None,
        }
        
        # Send to WebSocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'threat_map',
            {
                'type': 'send_threat_update',
                'data': threat_data
            }
        )
    except Exception as e:
        # Log the error but don't raise it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending threat map update: {str(e)}")


@receiver(post_save, sender=ScanThreat)
def update_scan_result_threat_level(sender, instance, created, **kwargs):
    """Update scan result threat level when a new threat is added."""
    if created:
        scan_result = instance.scan_result
        
        # Get all threats for this scan
        threats = scan_result.threats.all()
        
        # Determine highest severity
        severities = [threat.severity for threat in threats]
        
        # Update threat level if needed
        if ScanResult.ThreatLevel.CRITICAL in severities and scan_result.threat_level != ScanResult.ThreatLevel.CRITICAL:
            scan_result.threat_level = ScanResult.ThreatLevel.CRITICAL
            scan_result.save(update_fields=['threat_level'])
        elif ScanResult.ThreatLevel.HIGH in severities and scan_result.threat_level not in [ScanResult.ThreatLevel.CRITICAL, ScanResult.ThreatLevel.HIGH]:
            scan_result.threat_level = ScanResult.ThreatLevel.HIGH
            scan_result.save(update_fields=['threat_level'])
        elif ScanResult.ThreatLevel.MEDIUM in severities and scan_result.threat_level not in [ScanResult.ThreatLevel.CRITICAL, ScanResult.ThreatLevel.HIGH, ScanResult.ThreatLevel.MEDIUM]:
            scan_result.threat_level = ScanResult.ThreatLevel.MEDIUM
            scan_result.save(update_fields=['threat_level'])
        elif scan_result.threat_level == ScanResult.ThreatLevel.CLEAN:
            scan_result.threat_level = ScanResult.ThreatLevel.LOW
            scan_result.save(update_fields=['threat_level'])