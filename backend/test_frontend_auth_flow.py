#!/usr/bin/env python
import requests
import json
import time

def test_frontend_auth_endpoints():
    """Test the auth endpoints that the frontend uses"""
    base_url = "http://127.0.0.1:8000/api/auth"
    
    print("Testing Frontend Authentication Flow...\n")
    
    # Test 1: Registration with frontend format
    print("1. Testing registration with frontend data format...")
    registration_data = {
        'email': 'frontendtest@example.com',
        'username': 'frontenduser',
        'first_name': 'Frontend',
        'last_name': 'User',
        'password': 'securepassword123',
        'password_confirm': 'securepassword123',
        'organization': 'Test Org',
        'receive_updates': True
    }
    
    r = requests.post(f'{base_url}/register/', json=registration_data)
    print(f'Registration Status: {r.status_code}')
    if r.status_code != 201:
        print(f'Registration Error: {r.text}')
        return False
    else:
        print('✅ Registration successful!')
    
    # Test 2: Login with frontend format
    print("\n2. Testing login with frontend data format...")
    login_data = {
        'email': 'frontendtest@example.com',
        'password': 'securepassword123'
    }
    
    r2 = requests.post(f'{base_url}/login/', json=login_data)
    print(f'Login Status: {r2.status_code}')
    if r2.status_code != 200:
        print(f'Login Error: {r2.text}')
        return False
    else:
        print('✅ Login successful!')
        token_data = r2.json()
        access_token = token_data.get('access')
        print(f'Access token received: {access_token[:50]}...')
    
    # Test 3: Profile endpoint (used by frontend)
    print("\n3. Testing profile endpoint...")
    headers = {'Authorization': f'Bearer {access_token}'}
    r3 = requests.get(f'{base_url}/profile/', headers=headers)
    print(f'Profile Status: {r3.status_code}')
    if r3.status_code != 200:
        print(f'Profile Error: {r3.text}')
        return False
    else:
        print('✅ Profile endpoint working!')
        profile_data = r3.json()
        print(f'User: {profile_data.get("first_name")} {profile_data.get("last_name")} ({profile_data.get("email")})')
    
    # Test 4: Token refresh
    print("\n4. Testing token refresh...")
    refresh_token = token_data.get('refresh')
    refresh_data = {'refresh': refresh_token}
    r4 = requests.post(f'{base_url}/token/refresh/', json=refresh_data)
    print(f'Token Refresh Status: {r4.status_code}')
    if r4.status_code != 200:
        print(f'Token Refresh Error: {r4.text}')
        return False
    else:
        print('✅ Token refresh working!')
    
    print("\n🎉 All frontend authentication endpoints are working correctly!")
    return True

if __name__ == "__main__":
    test_frontend_auth_endpoints()