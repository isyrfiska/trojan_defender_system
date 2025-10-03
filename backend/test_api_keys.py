#!/usr/bin/env python3
"""
Test script to verify API key configuration and validity
"""
from dotenv import load_dotenv
import os
import requests
import sys

def main():
    # Load environment variables
    load_dotenv('.env.local')
    
    print('=== API Key Status Check ===')
    
    # Check VirusTotal API Key
    vt_key = os.getenv('VIRUSTOTAL_API_KEY')
    print(f'VirusTotal API Key: {vt_key[:20]}...' if vt_key else 'VirusTotal API Key: Not found')
    
    # Check Shodan API Key  
    shodan_key = os.getenv('SHODAN_API_KEY')
    print(f'Shodan API Key: {shodan_key[:20]}...' if shodan_key else 'Shodan API Key: Not found')
    
    # Check AbuseIPDB API Key
    abuse_key = os.getenv('ABUSEIPDB_API_KEY')
    print(f'AbuseIPDB API Key: {abuse_key[:20]}...' if abuse_key else 'AbuseIPDB API Key: Not found')
    
    print('\n=== Testing API Key Validity ===')
    
    # Test AbuseIPDB API
    if abuse_key:
        try:
            headers = {'Key': abuse_key, 'Accept': 'application/json'}
            response = requests.get('https://api.abuseipdb.com/api/v2/check?ipAddress=8.8.8.8&maxAgeInDays=90', headers=headers, timeout=10)
            status = 'Valid' if response.status_code == 200 else 'Invalid'
            print(f'AbuseIPDB Test: {response.status_code} - {status}')
        except Exception as e:
            print(f'AbuseIPDB Test: Error - {e}')
    
    # Test VirusTotal API (basic check)
    if vt_key:
        try:
            headers = {'x-apikey': vt_key}
            response = requests.get('https://www.virustotal.com/api/v3/domains/google.com', headers=headers, timeout=10)
            status = 'Valid' if response.status_code == 200 else 'Invalid'
            print(f'VirusTotal Test: {response.status_code} - {status}')
        except Exception as e:
            print(f'VirusTotal Test: Error - {e}')
    
    # Test Shodan API
    if shodan_key:
        try:
            response = requests.get(f'https://api.shodan.io/shodan/host/8.8.8.8?key={shodan_key}', timeout=10)
            status = 'Valid' if response.status_code == 200 else 'Invalid'
            print(f'Shodan Test: {response.status_code} - {status}')
        except Exception as e:
            print(f'Shodan Test: Error - {e}')
    
    print('\n=== Django Settings Test ===')
    
    # Test Django settings loading
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        vt_django = getattr(settings, 'VIRUSTOTAL_API_KEY', None)
        shodan_django = getattr(settings, 'SHODAN_API_KEY', None)
        abuse_django = getattr(settings, 'ABUSEIPDB_API_KEY', None)
        
        print(f'Django VirusTotal Key: {vt_django[:20]}...' if vt_django else 'Django VirusTotal Key: Not found')
        print(f'Django Shodan Key: {shodan_django[:20]}...' if shodan_django else 'Django Shodan Key: Not found')
        print(f'Django AbuseIPDB Key: {abuse_django[:20]}...' if abuse_django else 'Django AbuseIPDB Key: Not found')
        
    except Exception as e:
        print(f'Django settings test failed: {e}')

if __name__ == '__main__':
    main()