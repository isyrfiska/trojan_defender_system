#!/usr/bin/env python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url, method="GET", data=None, headers=None):
    """Test an API endpoint"""
    print(f"\n🔍 Testing {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Try to parse as JSON
        try:
            json_response = response.json()
            print(f"Response: {json.dumps(json_response, indent=2)}")
        except:
            print(f"Response (text): {response.text[:500]}...")
            
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing API endpoints...")
    
    # Test basic API root
    test_endpoint(f"{BASE_URL}/api/")
    
    # Test auth endpoints
    test_endpoint(f"{BASE_URL}/api/auth/")
    
    # Test login endpoint with POST
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    test_endpoint(f"{BASE_URL}/api/auth/login/", "POST", login_data)
    
    # Test chatbot endpoint
    test_endpoint(f"{BASE_URL}/api/chatbot/")