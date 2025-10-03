import hashlib
import subprocess
import tempfile
import os
from typing import Dict, List, Any
import yara


class ScannerService:
    """Service class for file scanning operations."""
    
    def __init__(self):
        self.clamav_available = self._check_clamav_availability()
        self.yara_rules = self._load_yara_rules()
    
    def _check_clamav_availability(self) -> bool:
        """Check if ClamAV is available on the system."""
        try:
            result = subprocess.run(['clamscan', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _load_yara_rules(self):
        """Load YARA rules for scanning."""
        try:
            # Try to load default YARA rules
            rules_path = os.path.join(os.path.dirname(__file__), 'yara_rules')
            if os.path.exists(rules_path):
                return yara.compile(filepath=rules_path)
            return None
        except Exception:
            return None
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def scan_with_clamav(self, file_path: str) -> Dict[str, Any]:
        """Scan file with ClamAV antivirus."""
        if not self.clamav_available:
            return {
                'is_clean': True,
                'threats': [],
                'output': 'ClamAV not available',
                'engine': 'clamav'
            }
        
        try:
            result = subprocess.run(
                ['clamscan', '--no-summary', file_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout.strip()
            threats = []
            is_clean = result.returncode == 0
            
            if not is_clean:
                # Parse threats from output
                for line in output.split('\n'):
                    if 'FOUND' in line:
                        # Extract threat name
                        parts = line.split(':')
                        if len(parts) >= 2:
                            threat_name = parts[1].strip().replace(' FOUND', '')
                            threats.append(threat_name)
            
            return {
                'is_clean': is_clean,
                'threats': threats,
                'output': output,
                'engine': 'clamav'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'is_clean': False,
                'threats': ['Scan timeout'],
                'output': 'Scan timed out after 5 minutes',
                'engine': 'clamav'
            }
        except Exception as e:
            return {
                'is_clean': False,
                'threats': [f'Scan error: {str(e)}'],
                'output': f'Error during scan: {str(e)}',
                'engine': 'clamav'
            }
    
    def scan_with_yara(self, file_path: str) -> Dict[str, Any]:
        """Scan file with YARA rules."""
        if not self.yara_rules:
            return {
                'is_clean': True,
                'threats': [],
                'output': 'YARA rules not available',
                'engine': 'yara'
            }
        
        try:
            matches = self.yara_rules.match(file_path)
            threats = [match.rule for match in matches]
            is_clean = len(threats) == 0
            
            return {
                'is_clean': is_clean,
                'threats': threats,
                'output': f'YARA scan completed. Matches: {len(matches)}',
                'engine': 'yara'
            }
            
        except Exception as e:
            return {
                'is_clean': False,
                'threats': [f'YARA scan error: {str(e)}'],
                'output': f'Error during YARA scan: {str(e)}',
                'engine': 'yara'
            }
    
    def comprehensive_scan(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive scan using multiple engines."""
        results = {
            'file_path': file_path,
            'file_hash': self.calculate_file_hash(file_path),
            'engines': {},
            'overall_clean': True,
            'all_threats': []
        }
        
        # ClamAV scan
        clamav_result = self.scan_with_clamav(file_path)
        results['engines']['clamav'] = clamav_result
        if not clamav_result['is_clean']:
            results['overall_clean'] = False
            results['all_threats'].extend(clamav_result['threats'])
        
        # YARA scan
        yara_result = self.scan_with_yara(file_path)
        results['engines']['yara'] = yara_result
        if not yara_result['is_clean']:
            results['overall_clean'] = False
            results['all_threats'].extend(yara_result['threats'])
        
        return results