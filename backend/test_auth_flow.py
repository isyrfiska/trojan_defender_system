#!/usr/bin/env python
import requests
import json

def test_registration_and_login():
    base_url = "http://127.0.0.1:8000/api/auth"
    
    # Test registration
    print("Testing registration with proper data...")
    registration_data = {
        'email': 'newtest@example.com',
        'password': 'securepassword123',
        'password_confirm': 'securepassword123',
        'first_name': 'New',
        'last_name': 'User'
    }
    
    r = requests.post(f'{base_url}/register/', json=registration_data)
    print(f'Registration Status: {r.status_code}')
    print(f'Registration Response: {r.text}')
    
    if r.status_code == 201:
        print('\n✅ Registration successful!')
        
        # Test login
        print('\nTesting login with new user...')
        login_data = {
            'email': 'newtest@example.com',
            'password': 'securepassword123'
        }
        
        r2 = requests.post(f'{base_url}/login/', json=login_data)
        print(f'Login Status: {r2.status_code}')
        print(f'Login Response: {r2.text}')
        
        if r2.status_code == 200:
            print('\n✅ Login successful!')
            token_data = r2.json()
            access_token = token_data.get('access')
            
            # Test user profile endpoint
            print('\nTesting user profile endpoint...')
            headers = {'Authorization': f'Bearer {access_token}'}
            r3 = requests.get(f'{base_url}/profile/', headers=headers)
            print(f'Profile Status: {r3.status_code}')
            print(f'Profile Response: {r3.text}')
            
        else:
            print('\n❌ Login failed!')
    else:
        print('\n❌ Registration failed!')
        
        # Try with existing user
        print('\nTrying login with existing admin user...')
        admin_login = {
            'email': 'admin@example.com',
            'password': 'admin123'
        }
        
        r4 = requests.post(f'{base_url}/login/', json=admin_login)
        print(f'Admin Login Status: {r4.status_code}')
        print(f'Admin Login Response: {r4.text}')

if __name__ == "__main__":
    test_registration_and_login()