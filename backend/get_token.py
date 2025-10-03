#!/usr/bin/env python
import requests
import json

# Superuser credentials
email = "admin@example.com"
password = "admin123"

BASE_URL = "http://127.0.0.1:8000"

def get_token():
    """Get JWT token for the superuser"""
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access')
        print(f"✅ Login successful")
        print(f"Access Token: {access_token}")
        return access_token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

if __name__ == "__main__":
    print("Getting JWT token for superuser...")
    
    token = get_token()
    if token:
        print(f"\n🔑 Use this token in your API tests:")
        print(f"Authorization: Bearer {token}")
    else:
        print("Failed to get token")