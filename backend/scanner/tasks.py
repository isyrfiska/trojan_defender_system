import os
import time
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ScanResult, ScanThreat, ScanStatistics
from .utils import (
    scan_with_clamav, 
    scan_with_yara, 
    scan_with_virustotal,
    determine_threat_level, 
    get_file_hash, 
    get_file_type
)

logger = logging.getLogger(__name__)


def send_scan_notification(user_id, data):
    """Send scan notification via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    'type': 'scan_notification',
                    **data
                }
            )
    except Exception as e:
        logger.error(f"Error sending WebSocket notification: {str(e)}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_file(self, scan_id):
    """
    Celery task to scan a file with enhanced error handling and retry logic.
    """
    import time
    from django.utils import timezone
    
    logger.info(f"Starting scan task for scan_id: {scan_id} (attempt {self.request.retries + 1})")
    
    try:
        # Get scan result with retry logic
        max_db_retries = 3
        retry_delay = 1
        scan_result = None
        
        for attempt in range(max_db_retries):
            try:
                scan_result = ScanResult.objects.get(id=scan_id)
                logger.info(f"Retrieved scan result for ID {scan_id} on attempt {attempt + 1}")
                break
            except ScanResult.DoesNotExist:
                if attempt == max_db_retries - 1:
                    logger.error(f"Scan result with ID {scan_id} not found after {max_db_retries} attempts")
                    raise
                logger.warning(f"Scan result not found on attempt {attempt + 1}, retrying...")
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as db_error:
                logger.error(f"Database error on attempt {attempt + 1}: {str(db_error)}")
                if attempt == max_db_retries - 1:
                    raise
                time.sleep(retry_delay)
                retry_delay *= 2
        
        # Update scan status to running
        scan_result.status = 'running'
        scan_result.started_at = timezone.now()
        scan_result.save()
        
        # Send status update
        try:
            send_scan_status_update(scan_id, 'running', 'Scan in progress...')
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket update: {str(ws_error)}")
        
        file_path = scan_result.storage_path
        
        # Validate file exists and is accessible
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            scan_result.status = 'failed'
            scan_result.error_message = error_msg
            scan_result.completed_at = timezone.now()
            scan_result.save()
            send_scan_status_update(scan_id, 'failed', error_msg)
            return
        
        if not os.access(file_path, os.R_OK):
            error_msg = f"File not readable: {file_path}"
            logger.error(error_msg)
            scan_result.status = 'failed'
            scan_result.error_message = error_msg
            scan_result.completed_at = timezone.now()
            scan_result.save()
            send_scan_status_update(scan_id, 'failed', error_msg)
            return
        
        logger.info(f"Scanning file: {file_path}")
        
        # Initialize scan results
        scan_results = {
            'clamav': {'status': 'skipped', 'threats': []},
            'yara': {'status': 'skipped', 'threats': []},
            'virustotal': {'status': 'skipped', 'threats': []}
        }
        
        # ClamAV scan with error handling
        try:
            logger.info("Starting ClamAV scan...")
            clamav_result = scan_with_clamav(file_path)
            scan_results['clamav'] = clamav_result
            logger.info(f"ClamAV scan completed: {clamav_result['status']}")
            
            if clamav_result['status'] == 'error':
                logger.warning(f"ClamAV scan error: {clamav_result['message']}")
            
        except Exception as clamav_error:
            logger.error(f"ClamAV scan exception: {str(clamav_error)}", exc_info=True)
            scan_results['clamav'] = {
                'status': 'error',
                'message': f'ClamAV scan failed: {str(clamav_error)}',
                'threats': []
            }
        
        # YARA scan with error handling
        try:
            logger.info("Starting YARA scan...")
            yara_result = scan_with_yara(file_path)
            scan_results['yara'] = yara_result
            logger.info(f"YARA scan completed: {yara_result['status']}")
            
            if yara_result['status'] == 'error':
                logger.warning(f"YARA scan error: {yara_result['message']}")
                
        except Exception as yara_error:
            logger.error(f"YARA scan exception: {str(yara_error)}", exc_info=True)
            scan_results['yara'] = {
                'status': 'error',
                'message': f'YARA scan failed: {str(yara_error)}',
                'threats': []
            }
        
        # VirusTotal scan with error handling (if enabled)
        virustotal_enabled = getattr(settings, 'VIRUSTOTAL_ENABLED', False)
        if virustotal_enabled:
            try:
                logger.info("Starting VirusTotal scan...")
                virustotal_result = scan_with_virustotal(file_path)
                scan_results['virustotal'] = virustotal_result
                logger.info(f"VirusTotal scan completed: {virustotal_result['status']}")
                
                if virustotal_result['status'] == 'error':
                    logger.warning(f"VirusTotal scan error: {virustotal_result['message']}")
                    
            except Exception as vt_error:
                logger.error(f"VirusTotal scan exception: {str(vt_error)}", exc_info=True)
                scan_results['virustotal'] = {
                    'status': 'error',
                    'message': f'VirusTotal scan failed: {str(vt_error)}',
                    'threats': []
                }
        else:
            logger.info("VirusTotal scanning disabled")
        
        # Determine overall threat level
        try:
            threat_level = determine_threat_level_with_virustotal(
                scan_results['clamav'],
                scan_results['yara'],
                scan_results['virustotal']
            )
            logger.info(f"Determined threat level: {threat_level}")
            
        except Exception as threat_error:
            logger.error(f"Error determining threat level: {str(threat_error)}", exc_info=True)
            threat_level = 'unknown'
        
        # Collect all threats
        all_threats = []
        for engine, result in scan_results.items():
            if result.get('threats'):
                all_threats.extend(result['threats'])
        
        # Update scan result
        try:
            scan_result.status = 'completed'
            scan_result.threat_level = threat_level
            scan_result.threats_found = len(all_threats)
            scan_result.scan_results = scan_results
            scan_result.completed_at = timezone.now()
            scan_result.error_message = None  # Clear any previous error
            scan_result.save()
            
            logger.info(f"Scan completed successfully for {file_path}: {threat_level} threat level, {len(all_threats)} threats")
            
        except Exception as save_error:
            logger.error(f"Failed to save scan results: {str(save_error)}", exc_info=True)
            # Try to update status to failed
            try:
                scan_result.status = 'failed'
                scan_result.error_message = f'Failed to save results: {str(save_error)}'
                scan_result.completed_at = timezone.now()
                scan_result.save()
            except Exception as final_save_error:
                logger.error(f"Failed to save error status: {str(final_save_error)}")
            
            send_scan_status_update(scan_id, 'failed', f'Failed to save results: {str(save_error)}')
            return
        
        # Send completion notification
        try:
            send_scan_status_update(scan_id, 'completed', f'Scan completed: {threat_level} threat level')
        except Exception as ws_error:
            logger.warning(f"Failed to send completion WebSocket update: {str(ws_error)}")
        
        logger.info(f"Scan task completed successfully for scan_id: {scan_id}")
        
    except ScanResult.DoesNotExist:
        error_msg = f"Scan result with ID {scan_id} not found"
        logger.error(error_msg)
        send_scan_status_update(scan_id, 'failed', error_msg)
        
    except Exception as e:
        error_msg = f"Scan task failed: {str(e)}"
        logger.error(f"Scan task error for scan_id {scan_id}: {error_msg}", exc_info=True)
        
        # Try to update scan result status
        try:
            scan_result = ScanResult.objects.get(id=scan_id)
            scan_result.status = 'failed'
            scan_result.error_message = error_msg
            scan_result.completed_at = timezone.now()
            scan_result.save()
        except Exception as update_error:
            logger.error(f"Failed to update scan result status: {str(update_error)}")
        
        # Send failure notification
        try:
            send_scan_status_update(scan_id, 'failed', error_msg)
        except Exception as ws_error:
            logger.warning(f"Failed to send failure WebSocket update: {str(ws_error)}")
        
        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying scan task for scan_id {scan_id} (retry {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=e)
        else:
            logger.error(f"Max retries exceeded for scan_id {scan_id}")
            raise


def determine_threat_level_with_virustotal(clamav_result, yara_result, virustotal_threats):
    """Determine overall threat level including VirusTotal results."""
    clamav_threats = len(clamav_result.get('threats', []))
    yara_threats = len(yara_result.get('threats', []))
    vt_threats = len(virustotal_threats)
    
    # Check for errors
    if (clamav_result.get('status') == 'error' and 
        yara_result.get('status') == 'error' and 
        vt_threats == 0):
        return 'unknown'
    
    # High threat: Any engine detected malware
    if (clamav_result.get('status') == 'infected' or 
        any(threat.get('severity') == 'high' for threat in virustotal_threats)):
        return 'high'
    
    # Medium threat: Multiple detections or suspicious patterns
    total_detections = clamav_threats + yara_threats + vt_threats
    
    if total_detections >= 3:
        return 'high'
    elif total_detections >= 1:
        # Check severity of detections
        high_severity_count = sum(
            1 for threat in yara_result.get('threats', [])
            if threat.get('severity') == 'high'
        ) + sum(
            1 for threat in virustotal_threats
            if threat.get('severity') == 'high'
        )
        
        if high_severity_count > 0:
            return 'high'
        elif total_detections >= 2:
            return 'medium'
        else:
            return 'low'
    
    # Clean: No threats detected
    return 'clean'


def send_scan_status_update(scan_id, status, message, **kwargs):
    """Send scan status update via WebSocket with error handling."""
    import time
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            channel_layer = get_channel_layer()
            
            if not channel_layer:
                logger.warning("Channel layer not available for WebSocket updates")
                return
            
            # Send to scan-specific group
            group_name = f"scan_{scan_id}"
            
            message_data = {
                'type': 'scan_status_update',
                'scan_id': scan_id,
                'status': status,
                'message': message,
                'timestamp': timezone.now().isoformat(),
                **kwargs
            }
            
            async_to_sync(channel_layer.group_send)(group_name, message_data)
            
            logger.info(f"Sent WebSocket update for scan {scan_id}: {status} - {message} (attempt {attempt + 1})")
            return
            
        except ImportError as import_error:
            logger.warning(f"WebSocket dependencies not available: {str(import_error)}")
            return
            
        except Exception as ws_error:
            logger.warning(f"WebSocket update attempt {attempt + 1} failed for scan {scan_id}: {str(ws_error)}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Failed to send WebSocket update after {max_retries} attempts for scan {scan_id}")
                return


@shared_task
def update_scan_statistics():
    """Update daily scan statistics."""
    try:
        today = timezone.now().date()
        
        # Get or create today's statistics
        stats, created = ScanStatistics.objects.get_or_create(
            date=today,
            defaults={
                'total_scans': 0,
                'clean_files': 0,
                'infected_files': 0,
                'threats_detected': 0,
                'avg_scan_duration': 0.0
            }
        )
        
        # Calculate statistics for today
        today_scans = ScanResult.objects.filter(scan_date__date=today)
        
        if today_scans.exists():
            stats.total_scans = today_scans.count()
            stats.clean_files = today_scans.filter(threat_level='clean').count()
            stats.infected_files = today_scans.exclude(threat_level='clean').count()
            stats.threats_detected = ScanThreat.objects.filter(scan_result__scan_date__date=today).count()
            
            # Calculate average scan duration
            completed_scans = today_scans.filter(
                status='completed',
                scan_duration__isnull=False
            )
            if completed_scans.exists():
                total_duration = sum(scan.scan_duration for scan in completed_scans)
                stats.avg_scan_duration = total_duration / completed_scans.count()
            
            stats.save()
        
        logger.info(f"Updated scan statistics for {today}")
        
    except Exception as e:
        logger.error(f"Error updating scan statistics: {str(e)}")


@shared_task
def cleanup_old_files():
    """Clean up old scan files and data."""
    try:
        # Delete files older than configured retention period
        retention_days = getattr(settings, 'SCAN_FILE_RETENTION_DAYS', 30)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        old_scans = ScanResult.objects.filter(upload_date__lt=cutoff_date)
        
        deleted_files = 0
        for scan in old_scans:
            if scan.storage_path and os.path.exists(scan.storage_path):
                try:
                    os.remove(scan.storage_path)
                    deleted_files += 1
                except OSError as e:
                    logger.warning(f"Could not delete file {scan.storage_path}: {str(e)}")
        
        # Delete old scan records
        deleted_scans = old_scans.count()
        old_scans.delete()
        
        logger.info(f"Cleanup completed: {deleted_scans} scan records and {deleted_files} files deleted")
        
        return {
            'deleted_scans': deleted_scans,
            'deleted_files': deleted_files
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise


@shared_task
def generate_daily_report():
    """Generate daily security report."""
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get yesterday's statistics
        try:
            stats = ScanStatistics.objects.get(date=yesterday)
        except ScanStatistics.DoesNotExist:
            logger.warning(f"No statistics found for {yesterday}")
            return
        
        # Generate report data
        report_data = {
            'date': yesterday.isoformat(),
            'total_scans': stats.total_scans,
            'clean_files': stats.clean_files,
            'infected_files': stats.infected_files,
            'threats_detected': stats.threats_detected,
            'avg_scan_duration': stats.avg_scan_duration,
            'infection_rate': (stats.infected_files / stats.total_scans * 100) if stats.total_scans > 0 else 0
        }
        
        # Here you could send the report via email, save to file, etc.
        logger.info(f"Daily report generated for {yesterday}: {report_data}")
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        raise