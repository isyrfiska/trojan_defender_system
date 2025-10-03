import os
import time
import hashlib
import logging
from typing import Dict, List, Optional
from django.conf import settings
import vt

logger = logging.getLogger(__name__)


class VirusTotalScanner:
    """VirusTotal API scanner for real malware detection."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'VIRUSTOTAL_API_KEY', None)
        if not self.api_key or self.api_key == 'your_virustotal_api_key_here':
            logger.error("VirusTotal API key not configured. Real-time scanning requires a valid API key.")
            raise ValueError("VirusTotal API key is required for real-time scanning")
        
        self.client = vt.Client(self.api_key)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'client'):
            self.client.close()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
    
    def scan_file(self, file_path: str) -> Dict:
        """
        Scan file using VirusTotal API.
        Returns scan results with threat information.
        """
        try:
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            if not file_hash:
                return {
                    'status': 'error',
                    'message': 'Failed to calculate file hash',
                    'threats': []
                }
            
            # First, try to get existing analysis
            try:
                file_obj = self.client.get_object(f"/files/{file_hash}")
                analysis_stats = file_obj.last_analysis_stats
                
                # If we have recent analysis, use it
                if analysis_stats:
                    return self._parse_analysis_results(file_obj, file_hash)
                    
            except vt.APIError as e:
                if e.code != "NotFoundError":
                    logger.error(f"VirusTotal API error: {str(e)}")
                    return {
                        'status': 'error',
                        'message': f'VirusTotal API error: {str(e)}',
                        'threats': []
                    }
            
            # If no existing analysis, upload file for scanning
            logger.info(f"Uploading file {file_path} to VirusTotal for analysis")
            
            with open(file_path, "rb") as f:
                analysis = self.client.scan_file(f)
            
            # Wait for analysis to complete (with timeout)
            analysis_id = analysis.id
            max_wait_time = 300  # 5 minutes
            wait_interval = 10   # 10 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                try:
                    analysis = self.client.get_object(f"/analyses/{analysis_id}")
                    
                    if hasattr(analysis, 'attributes') and analysis.attributes.get('status') == 'completed':
                        # Get the file object with analysis results
                        file_obj = self.client.get_object(f"/files/{file_hash}")
                        return self._parse_analysis_results(file_obj, file_hash)
                    
                    time.sleep(wait_interval)
                    elapsed_time += wait_interval
                    
                except vt.APIError as e:
                    logger.error(f"Error checking analysis status: {str(e)}")
                    break
            
            # If analysis didn't complete in time, return pending status
            return {
                'status': 'pending',
                'message': 'Analysis in progress. Results will be available shortly.',
                'threats': [],
                'analysis_id': analysis_id
            }
            
        except Exception as e:
            logger.error(f"VirusTotal scan error for {file_path}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'threats': []
            }
    
    def _parse_analysis_results(self, file_obj, file_hash: str) -> Dict:
        """Parse VirusTotal analysis results."""
        try:
            stats = file_obj.last_analysis_stats
            results = file_obj.last_analysis_results
            
            malicious_count = stats.get('malicious', 0)
            suspicious_count = stats.get('suspicious', 0)
            total_engines = sum(stats.values())
            
            threats = []
            
            # Extract threats from engines that detected malware
            if results:
                for engine_name, result in results.items():
                    if result.get('category') in ['malicious', 'suspicious']:
                        threat_name = result.get('result', 'Unknown threat')
                        threats.append({
                            'name': threat_name,
                            'threat_type': 'malware' if result.get('category') == 'malicious' else 'suspicious',
                            'description': f'Detected by {engine_name}: {threat_name}',
                            'location': file_hash,
                            'detection_engine': engine_name,
                            'detection_rule': threat_name,
                            'severity': 'high' if result.get('category') == 'malicious' else 'medium'
                        })
            
            # Determine overall status
            if malicious_count > 0:
                status = 'infected'
                message = f'Malware detected by {malicious_count}/{total_engines} engines'
            elif suspicious_count > 0:
                status = 'suspicious'
                message = f'Suspicious content detected by {suspicious_count}/{total_engines} engines'
            else:
                status = 'clean'
                message = f'No threats detected by {total_engines} engines'
            
            return {
                'status': status,
                'message': message,
                'threats': threats,
                'scan_stats': {
                    'malicious': malicious_count,
                    'suspicious': suspicious_count,
                    'clean': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'total_engines': total_engines
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing VirusTotal results: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to parse scan results: {str(e)}',
                'threats': []
            }
    
def scan_file_with_virustotal(file_path: str) -> Dict:
    """
    Convenience function to scan a file with VirusTotal.
    """
    with VirusTotalScanner() as scanner:
        return scanner.scan_file(file_path)