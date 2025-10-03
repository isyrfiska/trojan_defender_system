import requests
import os
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv()

api_key = os.environ.get('ABUSEIPDB_API_KEY')
headers = {
    'Key': api_key,
    'Accept': 'application/json',
}

url = 'https://api.abuseipdb.com/api/v2/blacklist'
params = {
    'confidenceMinimum': 25,
    'limit': 10,
    'plaintext': False
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("Content-Type")}')
print(f'Response text (first 200 chars): {response.text[:200]}')
print(f'Response is JSON: {"application/json" in response.headers.get("Content-Type", "")}')

# Try to parse as JSON
try:
    json_data = response.json()
    print(f'JSON parsing successful: {type(json_data)}')
    if isinstance(json_data, dict):
        print(f'JSON keys: {list(json_data.keys())}')
except Exception as e:
    print(f'JSON parsing failed: {e}')
    print('Raw response:')
    print(response.text[:500])