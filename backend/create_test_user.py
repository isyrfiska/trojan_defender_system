#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
django.setup()

from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# Create or get test user
user, created = User.objects.get_or_create(
    email='testuser@example.com',
    defaults={
        'first_name': 'Test',
        'last_name': 'User',
        'is_active': True
    }
)

if created:
    user.set_password('testpass123')
    user.save()
    print(f'Created new test user: {user.email}')
else:
    print(f'Using existing test user: {user.email}')

# Generate JWT token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f'\nAccess Token: {access_token}')
print(f'\nYou can now test the chatbot API with:')
print(f'Authorization: Bearer {access_token}')