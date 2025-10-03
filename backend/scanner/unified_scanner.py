import os
import logging
from datetime import datetime
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ScanResult, NetworkScan, NetworkThreat, ScanThreat
from .tasks import scan_file, analyze_pcap_file
from .ml_models import ThreatPredictionEngine
from .pcap_analyzer import PcapAnalyzer  # Fixed: Changed PCAPAnalyzer to PcapAnalyzer
from .utils import scan_with_clamav, scan_with_yara

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class UnifiedScannerService:
    """Unified service for handling both file and network scans with real-time processing."""
    
    def __init__(self):
        self.ml_engine = ThreatPredictionEngine()
        # Removed: self.pcap_analyzer = PcapAnalyzer() - not used and requires pcap_file_path parameter
    
    def start_unified_scan(self, user, scan_type, file_path, **kwargs):
        """Start a unified scan (file or network) with real-time updates."""
        try:
            if scan_type == 'file':
                return self._start_file_scan(user, file_path, **kwargs)
            elif scan_type == 'network':
                return self._start_network_scan(user, file_path, **kwargs)
            else:
                raise ValueError(f"Unsupported scan type: {scan_type}")
        except Exception as e:
            logger.error(f"Error starting unified scan: {str(e)}")
            raise
    
    def _start_file_scan(self, user, file_path, **kwargs):
        """Start file scan with real-time updates."""
        # Create scan result
        scan_result = ScanResult.objects.create(
            user=user,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            file_type=kwargs.get('file_type', 'unknown'),
            file_hash=kwargs.get('file_hash', ''),
            storage_path=file_path
        )
        
        # Send initial status
        self._send_scan_update(scan_result.id, 'file', {
            'status': 'started',
            'message': 'File scan initiated',
            'scan_id': str(scan_result.id)
        })
        
        # Start async scan
        task = scan_file.delay(str(scan_result.id), file_path)
        
        return {
            'scan_id': scan_result.id,
            'task_id': task.id,
            'scan_type': 'file'
        }
    
    def _start_network_scan(self, user, file_path, **kwargs):
        """Start network scan with real-time updates."""
        # Create network scan
        network_scan = NetworkScan.objects.create(
            user=user,
            file_name=os.path.basename(file_path),
            file_size=os.path.getsize(file_path),
            scan_type=kwargs.get('scan_type', NetworkScan.ScanType.PCAP)
        )
        
        # Send initial status
        self._send_scan_update(network_scan.id, 'network', {
            'status': 'started',
            'message': 'Network analysis initiated',
            'scan_id': str(network_scan.id)
        })
        
        # Start async analysis
        task = analyze_pcap_file.delay(str(network_scan.id), file_path)
        
        return {
            'scan_id': network_scan.id,
            'task_id': task.id,
            'scan_type': 'network'
        }
    
    def process_realtime_network_data(self, user, network_data):
        """Process real-time network data stream."""
        try:
            # Create live capture scan
            network_scan = NetworkScan.objects.create(
                user=user,
                file_name='live_capture',
                file_size=0,
                scan_type=NetworkScan.ScanType.LIVE_CAPTURE,
                status=ScanResult.ScanStatus.SCANNING
            )
            
            # Process packets in real-time
            threats_detected = []
            packet_count = 0
            
            for packet_data in network_data:
                packet_count += 1
                
                # Analyze packet for threats
                threat_analysis = self._analyze_packet_realtime(packet_data)
                
                if threat_analysis['is_threat']:
                    # Create threat record
                    threat = NetworkThreat.objects.create(
                        network_scan=network_scan,
                        threat_category=threat_analysis['category'],
                        source_ip=threat_analysis['source_ip'],
                        destination_ip=threat_analysis['destination_ip'],
                        protocol=threat_analysis['protocol'],
                        threat_name=threat_analysis['name'],
                        description=threat_analysis['description'],
                        severity=threat_analysis['severity'],
                        confidence_score=threat_analysis['confidence'],
                        first_seen=timezone.now(),
                        last_seen=timezone.now()
                    )
                    threats_detected.append(threat)
                    
                    # Send real-time threat alert
                    self._send_realtime_threat_alert(network_scan.id, threat_analysis)
                
                # Send periodic updates every 100 packets
                if packet_count % 100 == 0:
                    self._send_realtime_update(network_scan.id, {
                        'packets_processed': packet_count,
                        'threats_detected': len(threats_detected),
                        'current_threat_level': self._calculate_current_threat_level(threats_detected)
                    })
            
            # Finalize scan
            network_scan.total_packets = packet_count
            network_scan.status = ScanResult.ScanStatus.COMPLETED
            network_scan.analysis_date = timezone.now()
            network_scan.save()
            
            return {
                'scan_id': network_scan.id,
                'packets_processed': packet_count,
                'threats_detected': len(threats_detected)
            }
            
        except Exception as e:
            logger.error(f"Error processing real-time network data: {str(e)}")
            raise
    
    def _analyze_packet_realtime(self, packet_data):
        """Analyze individual packet for threats in real-time."""
        # Implement real-time packet analysis logic
        # This would use ML models and threat intelligence
        
        # Placeholder implementation
        return {
            'is_threat': False,
            'category': NetworkThreat.ThreatCategory.PROTOCOL_ANOMALY,
            'source_ip': packet_data.get('src_ip', ''),
            'destination_ip': packet_data.get('dst_ip', ''),
            'protocol': packet_data.get('protocol', ''),
            'name': 'Unknown Threat',
            'description': 'Threat detected in real-time analysis',
            'severity': ScanResult.ThreatLevel.LOW,
            'confidence': 0.5
        }
    
    def _calculate_current_threat_level(self, threats):
        """Calculate current threat level based on detected threats."""
        if not threats:
            return ScanResult.ThreatLevel.CLEAN
        
        # Simple logic - can be enhanced with ML
        high_severity_count = sum(1 for t in threats if t.severity == ScanResult.ThreatLevel.HIGH)
        critical_count = sum(1 for t in threats if t.severity == ScanResult.ThreatLevel.CRITICAL)
        
        if critical_count > 0:
            return ScanResult.ThreatLevel.CRITICAL
        elif high_severity_count > 2:
            return ScanResult.ThreatLevel.HIGH
        elif len(threats) > 5:
            return ScanResult.ThreatLevel.MEDIUM
        else:
            return ScanResult.ThreatLevel.LOW
    
    def _send_scan_update(self, scan_id, scan_type, data):
        """Send scan status update via WebSocket."""
        async_to_sync(channel_layer.group_send)(
            f'{scan_type}_scan_{scan_id}',
            {
                'type': 'send_update',
                'data': data
            }
        )
    
    def _send_realtime_update(self, scan_id, data):
        """Send real-time update via WebSocket."""
        async_to_sync(channel_layer.group_send)(
            f'network_scan_{scan_id}',
            {
                'type': 'send_realtime_update',
                'data': data
            }
        )
    
    def _send_realtime_threat_alert(self, scan_id, threat_data):
        """Send immediate threat alert via WebSocket."""
        async_to_sync(channel_layer.group_send)(
            f'network_scan_{scan_id}',
            {
                'type': 'send_realtime_update',
                'data': {
                    'type': 'threat_alert',
                    'threat': threat_data,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )