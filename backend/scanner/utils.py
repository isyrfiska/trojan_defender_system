import os
import hashlib
import mimetypes
import yara
import pyclamd
import logging
from django.conf import settings
from .models import YaraRule, ScanThreat
from .virustotal_scanner import scan_file_with_virustotal

# Try to import python-magic, fallback to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, using mimetypes for file type detection")

logger = logging.getLogger(__name__)

def get_file_hash(file_path, algorithm='sha256'):
    """Calculate file hash using specified algorithm."""
    hash_func = getattr(hashlib, algorithm)()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return None

def get_file_type(file_path):
    """Detect file type using python-magic or mimetypes as fallback."""
    try:
        if MAGIC_AVAILABLE:
            return magic.from_file(file_path, mime=True)
        else:
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'
    except Exception as e:
        logger.error(f"Error detecting file type for {file_path}: {str(e)}")
        return 'application/octet-stream'

def scan_with_clamav(file_path):
    """Scan file with ClamAV antivirus."""
    import time
    
    try:
        # Connect to ClamAV daemon with retry logic
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                cd = pyclamd.ClamdAgnostic(
                    host=getattr(settings, 'SCANNER_HOST', 'scanner'),
                    port=getattr(settings, 'SCANNER_PORT', 3310),
                    timeout=30
                )
                
                # Test connection
                if cd.ping():
                    logger.info(f"ClamAV connection successful on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"ClamAV ping failed on attempt {attempt + 1}")
                    
            except Exception as conn_error:
                logger.warning(f"ClamAV connection attempt {attempt + 1} failed: {str(conn_error)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"ClamAV connection failed after {max_retries} attempts")
                    return {
                        'status': 'error',
                        'message': f'ClamAV daemon not available after {max_retries} attempts: {str(conn_error)}',
                        'threats': []
                    }
        
        # Verify file exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"File not found for ClamAV scan: {file_path}")
            return {
                'status': 'error',
                'message': f'File not found: {file_path}',
                'threats': []
            }
        
        if not os.access(file_path, os.R_OK):
            logger.error(f"File not readable for ClamAV scan: {file_path}")
            return {
                'status': 'error',
                'message': f'File not readable: {file_path}',
                'threats': []
            }
        
        # Scan file
        logger.info(f"Starting ClamAV scan for: {file_path}")
        result = cd.scan_file(file_path)
        
        if result is None:
            logger.info(f"ClamAV scan completed - no threats found: {file_path}")
            return {
                'status': 'clean',
                'message': 'No threats detected by ClamAV',
                'threats': []
            }
        
        # Parse ClamAV result
        threats = []
        for file_path_result, threat_info in result.items():
            if threat_info[0] == 'FOUND':
                threat = {
                    'name': threat_info[1],
                    'threat_type': 'malware',
                    'description': f'ClamAV detected: {threat_info[1]}',
                    'location': file_path_result,
                    'detection_engine': 'ClamAV',
                    'detection_rule': threat_info[1],
                    'severity': 'high'
                }
                threats.append(threat)
                logger.warning(f"ClamAV threat detected: {threat_info[1]} in {file_path_result}")
        
        status = 'infected' if threats else 'clean'
        message = f'ClamAV scan completed. Found {len(threats)} threats.'
        
        logger.info(f"ClamAV scan result for {file_path}: {status}, {len(threats)} threats")
        
        return {
            'status': status,
            'message': message,
            'threats': threats
        }
        
    except Exception as e:
        logger.error(f"ClamAV scan error for {file_path}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f'ClamAV scan failed: {str(e)}',
            'threats': []
        }

def compile_yara_rules():
    """Compile all active YARA rules."""
    import time
    
    try:
        from .models import YaraRule
        
        # Get all active rules with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                active_rules = YaraRule.objects.filter(is_active=True)
                logger.info(f"Found {active_rules.count()} active YARA rules on attempt {attempt + 1}")
                break
            except Exception as db_error:
                logger.warning(f"Database query attempt {attempt + 1} failed: {str(db_error)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Failed to fetch YARA rules after {max_retries} attempts")
                    return None
        
        if not active_rules.exists():
            logger.warning("No active YARA rules found")
            return None
        
        # Prepare rules dictionary with validation
        rules_dict = {}
        invalid_rules = []
        
        for rule in active_rules:
            try:
                # Validate rule content
                if not rule.rule_content or not rule.rule_content.strip():
                    logger.warning(f"Empty rule content for rule: {rule.name}")
                    invalid_rules.append(rule.name)
                    continue
                
                # Basic syntax validation
                if 'rule ' not in rule.rule_content:
                    logger.warning(f"Invalid YARA rule syntax for rule: {rule.name}")
                    invalid_rules.append(rule.name)
                    continue
                
                rules_dict[rule.name] = rule.rule_content
                logger.debug(f"Added YARA rule to compilation: {rule.name}")
                
            except Exception as rule_error:
                logger.error(f"Error processing YARA rule {rule.name}: {str(rule_error)}")
                invalid_rules.append(rule.name)
                continue
        
        if invalid_rules:
            logger.warning(f"Skipped {len(invalid_rules)} invalid YARA rules: {', '.join(invalid_rules)}")
        
        if not rules_dict:
            logger.error("No valid YARA rules available for compilation")
            return None
        
        # Compile rules with error handling
        try:
            logger.info(f"Compiling {len(rules_dict)} YARA rules...")
            compiled_rules = yara.compile(sources=rules_dict)
            logger.info(f"Successfully compiled {len(rules_dict)} YARA rules")
            return compiled_rules
            
        except yara.SyntaxError as syntax_error:
            logger.error(f"YARA syntax error during compilation: {str(syntax_error)}")
            
            # Try to identify problematic rule
            for rule_name, rule_content in rules_dict.items():
                try:
                    yara.compile(source=rule_content)
                except yara.SyntaxError:
                    logger.error(f"Syntax error in YARA rule: {rule_name}")
                    
            return None
            
        except yara.Error as yara_error:
            logger.error(f"YARA compilation error: {str(yara_error)}")
            return None
            
    except ImportError as import_error:
        logger.error(f"Failed to import required modules: {str(import_error)}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error compiling YARA rules: {str(e)}", exc_info=True)
        return None

def scan_with_yara(file_path):
    """Scan file with YARA rules."""
    import time
    
    try:
        # Compile YARA rules with retry logic
        max_retries = 3
        retry_delay = 1
        compiled_rules = None
        
        for attempt in range(max_retries):
            try:
                compiled_rules = compile_yara_rules()
                if compiled_rules:
                    logger.info(f"YARA rules compiled successfully on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"YARA rule compilation returned None on attempt {attempt + 1}")
                    
            except Exception as compile_error:
                logger.warning(f"YARA compilation attempt {attempt + 1} failed: {str(compile_error)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"YARA rule compilation failed after {max_retries} attempts")
                    return {
                        'status': 'error',
                        'message': f'YARA rules compilation failed after {max_retries} attempts',
                        'threats': []
                    }
        
        if not compiled_rules:
            logger.warning("No YARA rules available for scanning")
            return {
                'status': 'clean',
                'message': 'No YARA rules available for scanning',
                'threats': []
            }
        
        # Verify file exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"File not found for YARA scan: {file_path}")
            return {
                'status': 'error',
                'message': f'File not found: {file_path}',
                'threats': []
            }
        
        if not os.access(file_path, os.R_OK):
            logger.error(f"File not readable for YARA scan: {file_path}")
            return {
                'status': 'error',
                'message': f'File not readable: {file_path}',
                'threats': []
            }
        
        # Check file size (avoid scanning very large files)
        try:
            file_size = os.path.getsize(file_path)
            max_file_size = getattr(settings, 'YARA_MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB default
            
            if file_size > max_file_size:
                logger.warning(f"File too large for YARA scan: {file_size} bytes (max: {max_file_size})")
                return {
                    'status': 'skipped',
                    'message': f'File too large for YARA scan: {file_size} bytes',
                    'threats': []
                }
        except OSError as size_error:
            logger.error(f"Could not determine file size: {str(size_error)}")
        
        # Scan file with YARA
        logger.info(f"Starting YARA scan for: {file_path}")
        
        try:
            matches = compiled_rules.match(file_path, timeout=60)
            logger.info(f"YARA scan completed for {file_path}: {len(matches)} matches found")
            
        except yara.TimeoutError:
            logger.warning(f"YARA scan timeout for file: {file_path}")
            return {
                'status': 'error',
                'message': 'YARA scan timeout',
                'threats': []
            }
        except yara.Error as yara_error:
            logger.error(f"YARA scan error for {file_path}: {str(yara_error)}")
            return {
                'status': 'error',
                'message': f'YARA scan error: {str(yara_error)}',
                'threats': []
            }
        
        # Process matches
        threats = []
        
        for match in matches:
            try:
                # Extract match details
                rule_name = match.rule
                namespace = getattr(match, 'namespace', 'default')
                tags = list(match.tags) if match.tags else []
                
                # Determine severity based on tags
                severity = 'medium'  # default
                if any(tag.lower() in ['critical', 'high', 'malware', 'trojan', 'virus'] for tag in tags):
                    severity = 'high'
                elif any(tag.lower() in ['low', 'info', 'suspicious'] for tag in tags):
                    severity = 'low'
                
                # Extract string matches
                string_matches = []
                for string_match in match.strings:
                    string_matches.append({
                        'identifier': string_match.identifier,
                        'instances': [
                            {
                                'offset': instance.offset,
                                'matched_data': instance.matched_data.decode('utf-8', errors='replace')[:100],  # Limit length
                                'matched_length': instance.matched_length
                            }
                            for instance in string_match.instances[:5]  # Limit instances
                        ]
                    })
                
                threat = {
                    'name': rule_name,
                    'threat_type': 'pattern_match',
                    'description': f'YARA rule match: {rule_name}',
                    'location': file_path,
                    'detection_engine': 'YARA',
                    'detection_rule': rule_name,
                    'severity': severity,
                    'namespace': namespace,
                    'tags': tags,
                    'string_matches': string_matches
                }
                
                threats.append(threat)
                logger.info(f"YARA threat detected: {rule_name} (severity: {severity}) in {file_path}")
                
            except Exception as match_error:
                logger.error(f"Error processing YARA match {match.rule}: {str(match_error)}")
                continue
        
        # Create threat entries in database
        if threats:
            try:
                from .models import Threat
                
                for threat_data in threats:
                    try:
                        Threat.objects.create(
                            name=threat_data['name'],
                            threat_type=threat_data['threat_type'],
                            description=threat_data['description'],
                            severity=threat_data['severity'],
                            detection_engine='YARA',
                            detection_rule=threat_data['detection_rule'],
                            file_path=file_path,
                            metadata={
                                'namespace': threat_data.get('namespace'),
                                'tags': threat_data.get('tags', []),
                                'string_matches': threat_data.get('string_matches', [])
                            }
                        )
                        logger.debug(f"Created threat entry for: {threat_data['name']}")
                        
                    except Exception as db_error:
                        logger.error(f"Failed to create threat entry for {threat_data['name']}: {str(db_error)}")
                        
            except ImportError as import_error:
                logger.warning(f"Could not import Threat model: {str(import_error)}")
        
        status = 'infected' if threats else 'clean'
        message = f'YARA scan completed. Found {len(threats)} threats.'
        
        logger.info(f"YARA scan result for {file_path}: {status}, {len(threats)} threats")
        
        return {
            'status': status,
            'message': message,
            'threats': threats
        }
        
    except Exception as e:
        logger.error(f"YARA scan error for {file_path}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f'YARA scan failed: {str(e)}',
            'threats': []
        }

def determine_threat_level(clamav_result, yara_result):
    """Determine overall threat level based on scan results."""
    clamav_threats = len(clamav_result.get('threats', []))
    yara_threats = len(yara_result.get('threats', []))
    
    # Check for errors
    if (clamav_result.get('status') == 'error' and 
        yara_result.get('status') == 'error'):
        return 'unknown'
    
    # High threat: ClamAV detected malware
    if clamav_result.get('status') == 'infected':
        return 'high'
    
    # Medium threat: YARA detected suspicious patterns
    if yara_result.get('status') == 'suspicious':
        # Check severity of YARA matches
        high_severity_count = sum(
            1 for threat in yara_result.get('threats', [])
            if threat.get('severity') == 'high'
        )
        
        if high_severity_count > 0:
            return 'high'
        elif yara_threats >= 3:
            return 'medium'
        else:
            return 'low'
    
    # Clean: No threats detected
    return 'clean'

def validate_file_upload(file):
    """Validate uploaded file before scanning."""
    errors = []
    
    # Check file size
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 104857600)  # 100MB default
    if file.size > max_size:
        errors.append(f'File size ({file.size} bytes) exceeds maximum allowed size ({max_size} bytes)')
    
    # Check file extension (basic validation)
    dangerous_extensions = ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js']
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension in dangerous_extensions:
        # Allow but warn about potentially dangerous files
        logger.warning(f"Potentially dangerous file uploaded: {file.name}")
    
    return errors

def scan_with_virustotal(file_path):
    """
    Scan file using VirusTotal API.
    Returns threats found by VirusTotal.
    """
    try:
        result = scan_file_with_virustotal(file_path)
        
        if result['status'] == 'error':
            logger.error(f"VirusTotal scan error: {result['message']}")
            return []
        
        if result['status'] == 'pending':
            logger.info(f"VirusTotal scan pending: {result['message']}")
            return []
        
        return result.get('threats', [])
        
    except Exception as e:
        logger.error(f"VirusTotal scan failed for {file_path}: {str(e)}")
        return []