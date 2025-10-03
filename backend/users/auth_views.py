from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer, CustomTokenObtainPairSerializer, AlternativeTokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

# Security logger
security_logger = logging.getLogger('django.security')


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
@method_decorator(swagger_auto_schema(
    operation_id='loginUser',
    operation_description='Login user and obtain JWT token pair',
    responses={200: 'Token pair obtained successfully', 401: 'Invalid credentials'}
), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with rate limiting and logging."""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Get user data and include it in response
            from django.contrib.auth import authenticate
            user = authenticate(
                request,
                username=request.data.get('email'),
                password=request.data.get('password')
            )
            if user:
                user_serializer = UserSerializer(user)
                response.data['user'] = user_serializer.data
                
            security_logger.info(f'Successful login for user: {request.data.get("email", "unknown")} from IP: {request.META.get("REMOTE_ADDR")}')
        else:
            security_logger.warning(f'Failed login attempt for user: {request.data.get("email", "unknown")} from IP: {request.META.get("REMOTE_ADDR")}')
        
        return response


@method_decorator(swagger_auto_schema(
    operation_id='obtainToken',
    operation_description='Obtain JWT token pair',
    responses={200: 'Token pair obtained successfully', 401: 'Invalid credentials'}
), name='post')
@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class AlternativeTokenObtainPairView(TokenObtainPairView):
    """Alternative token obtain view for /api/auth/token/ endpoint."""
    serializer_class = AlternativeTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Get user data and include it in response
            from django.contrib.auth import authenticate
            user = authenticate(
                request,
                username=request.data.get('email'),
                password=request.data.get('password')
            )
            if user:
                user_serializer = UserSerializer(user)
                response.data['user'] = user_serializer.data
                
            security_logger.info(f'Successful token obtain for user: {request.data.get("email", "unknown")} from IP: {request.META.get("REMOTE_ADDR")}')
        else:
            security_logger.warning(f'Failed token obtain attempt for user: {request.data.get("email", "unknown")} from IP: {request.META.get("REMOTE_ADDR")}')
        
        return response


@method_decorator(ratelimit(key='ip', rate='20/m', method='POST', block=True), name='post')
class CustomTokenRefreshView(TokenRefreshView):
    """Custom JWT token refresh view with rate limiting and logging."""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            security_logger.info(f'Token refreshed from IP: {request.META.get("REMOTE_ADDR")}')
        else:
            security_logger.warning(f'Failed token refresh attempt from IP: {request.META.get("REMOTE_ADDR")}')
        
        return response