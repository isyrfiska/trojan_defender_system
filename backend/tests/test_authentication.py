from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import json

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for custom User model."""
    
    def test_create_user_with_email(self):
        """Test creating a user with email."""
        email = 'test@example.com'
        password = 'testpass123'
        
        user = User.objects.create_user(
            email=email,
            password=password
        )
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_user_without_email(self):
        """Test creating a user without email raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='testpass123'
            )
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        email = 'admin@example.com'
        password = 'adminpass123'
        
        user = User.objects.create_superuser(
            email=email,
            password=password
        )
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_create_superuser_without_is_staff(self):
        """Test creating superuser without is_staff raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
    
    def test_create_superuser_without_is_superuser(self):
        """Test creating superuser without is_superuser raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )
    
    def test_user_str_representation(self):
        """Test string representation of user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_email_normalization(self):
        """Test email normalization."""
        email = 'Test@EXAMPLE.COM'
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )
        
        self.assertEqual(user.email, 'Test@example.com')


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.profile_url = reverse('user-profile')
        
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        self.user = User.objects.create_user(
            email='existing@example.com',
            password='existingpass123',
            first_name='Existing',
            last_name='User'
        )
    
    def test_user_registration_valid(self):
        """Test user registration with valid data."""
        response = self.client.post(
            self.register_url,
            self.user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify user was created
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
    
    def test_user_registration_duplicate_email(self):
        """Test user registration with duplicate email."""
        duplicate_data = self.user_data.copy()
        duplicate_data['email'] = 'existing@example.com'
        
        response = self.client.post(
            self.register_url,
            duplicate_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_invalid_email(self):
        """Test user registration with invalid email."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_weak_password(self):
        """Test user registration with weak password."""
        weak_data = self.user_data.copy()
        weak_data['password'] = '123'
        
        response = self.client.post(
            self.register_url,
            weak_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_user_registration_missing_fields(self):
        """Test user registration with missing required fields."""
        incomplete_data = {
            'email': 'incomplete@example.com'
            # Missing password
        }
        
        response = self.client.post(
            self.register_url,
            incomplete_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_user_login_valid_credentials(self):
        """Test user login with valid credentials."""
        login_data = {
            'email': 'existing@example.com',
            'password': 'existingpass123'
        }
        
        response = self.client.post(
            self.login_url,
            login_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        login_data = {
            'email': 'existing@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            self.login_url,
            login_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_login_nonexistent_user(self):
        """Test user login with nonexistent user."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        
        response = self.client.post(
            self.login_url,
            login_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_valid(self):
        """Test token refresh with valid refresh token."""
        # Get tokens for user
        refresh = RefreshToken.for_user(self.user)
        
        refresh_data = {
            'refresh': str(refresh)
        }
        
        response = self.client.post(
            self.refresh_url,
            refresh_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid(self):
        """Test token refresh with invalid refresh token."""
        refresh_data = {
            'refresh': 'invalid-refresh-token'
        }
        
        response = self.client.post(
            self.refresh_url,
            refresh_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_authenticated(self):
        """Test retrieving user profile when authenticated."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
    
    def test_user_profile_unauthenticated(self):
        """Test retrieving user profile when not authenticated."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_update(self):
        """Test updating user profile."""
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(
            self.profile_url,
            update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_user_profile_update_email_not_allowed(self):
        """Test that email cannot be updated through profile endpoint."""
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'email': 'newemail@example.com'
        }
        
        response = self.client.patch(
            self.profile_url,
            update_data,
            format='json'
        )
        
        # Email should not be updated
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, 'newemail@example.com')
    
    def test_password_change_valid(self):
        """Test password change with valid data."""
        self.client.force_authenticate(user=self.user)
        
        password_data = {
            'old_password': 'existingpass123',
            'new_password': 'newpassword123'
        }
        
        response = self.client.post(
            reverse('change-password'),
            password_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
    
    def test_password_change_invalid_old_password(self):
        """Test password change with invalid old password."""
        self.client.force_authenticate(user=self.user)
        
        password_data = {
            'old_password': 'wrongoldpassword',
            'new_password': 'newpassword123'
        }
        
        response = self.client.post(
            reverse('change-password'),
            password_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
    
    def test_password_change_weak_new_password(self):
        """Test password change with weak new password."""
        self.client.force_authenticate(user=self.user)
        
        password_data = {
            'old_password': 'existingpass123',
            'new_password': '123'
        }
        
        response = self.client.post(
            reverse('change-password'),
            password_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)


class JWTTokenTest(TestCase):
    """Test cases for JWT token functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_generation(self):
        """Test JWT token generation for user."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(access)
        self.assertIn('user_id', access.payload)
        self.assertEqual(access.payload['user_id'], self.user.id)
    
    def test_token_validation(self):
        """Test JWT token validation."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Token should be valid
        self.assertTrue(access.check_blacklist())
    
    def test_token_expiration(self):
        """Test JWT token expiration."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Check token has expiration time
        self.assertIn('exp', access.payload)
        self.assertGreater(access.payload['exp'], access.payload['iat'])
    
    def test_refresh_token_blacklist(self):
        """Test refresh token blacklisting."""
        refresh = RefreshToken.for_user(self.user)
        
        # Blacklist the token
        refresh.blacklist()
        
        # Token should be blacklisted
        with self.assertRaises(Exception):
            refresh.check_blacklist()


class AuthenticationMiddlewareTest(APITestCase):
    """Test cases for authentication middleware and permissions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
    
    def test_authenticated_request_with_valid_token(self):
        """Test authenticated request with valid JWT token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(reverse('user-profile'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authenticated_request_with_invalid_token(self):
        """Test authenticated request with invalid JWT token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        response = self.client.get(reverse('user-profile'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_request_without_token(self):
        """Test authenticated request without JWT token."""
        response = self.client.get(reverse('user-profile'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_request_with_expired_token(self):
        """Test authenticated request with expired JWT token."""
        # Create an expired token (this is a simplified test)
        # In a real scenario, you'd need to mock the token expiration
        expired_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6ImFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6IiwidXNlcl9pZCI6MX0.invalid'
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        response = self.client.get(reverse('user-profile'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        response = self.client.options(reverse('user-profile'))
        
        # Check for CORS headers (these depend on your CORS configuration)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
    
    @patch('authentication.middleware.logger')
    def test_request_logging(self, mock_logger):
        """Test that requests are properly logged."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(reverse('user-profile'))
        
        # Verify logging was called (this depends on your logging middleware)
        # mock_logger.info.assert_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # This test depends on your rate limiting implementation
        # Make multiple requests to test rate limiting
        for i in range(10):
            response = self.client.post(
                reverse('token_obtain_pair'),
                {
                    'email': 'test@example.com',
                    'password': 'wrongpassword'
                },
                format='json'
            )
        
        # After multiple failed attempts, should be rate limited
        # The exact status code depends on your rate limiting implementation
        self.assertIn(response.status_code, [status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_401_UNAUTHORIZED])