import logging
import time
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django_ratelimit.decorators import ratelimit
import json

# Set up logging
security_logger = logging.getLogger('security')
auth_logger = logging.getLogger('authentication')

User = get_user_model()

@method_decorator(never_cache, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='30/m', method='POST', block=True), name='post')
class EnhancedTokenRefreshView(TokenRefreshView):
    """
    Enhanced JWT token refresh view with comprehensive logging, 
    error handling, and security monitoring.
    """
    
    def post(self, request, *args, **kwargs):
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Log refresh attempt
        auth_logger.info(
            f'Token refresh attempt from IP: {client_ip}, '
            f'User-Agent: {user_agent[:100]}'
        )
        
        try:
            # Validate refresh token before processing
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                auth_logger.warning(
                    f'Token refresh failed - no refresh token provided from IP: {client_ip}'
                )
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Attempt to decode and validate the refresh token
            try:
                token = RefreshToken(refresh_token)
                user_id = token.payload.get('user_id')
                
                # Check if user exists and is active
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        if not user.is_active:
                            auth_logger.warning(
                                f'Token refresh failed - inactive user {user.email} from IP: {client_ip}'
                            )
                            return Response(
                                {'error': 'User account is inactive'}, 
                                status=status.HTTP_401_UNAUTHORIZED
                            )
                    except User.DoesNotExist:
                        auth_logger.warning(
                            f'Token refresh failed - user not found (ID: {user_id}) from IP: {client_ip}'
                        )
                        return Response(
                            {'error': 'User not found'}, 
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                
            except TokenError as e:
                auth_logger.warning(
                    f'Token refresh failed - invalid token from IP: {client_ip}, Error: {str(e)}'
                )
                return Response(
                    {'error': 'Invalid refresh token'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Process the refresh request
            response = super().post(request, *args, **kwargs)
            processing_time = time.time() - start_time
            
            if response.status_code == status.HTTP_200_OK:
                # Log successful refresh
                auth_logger.info(
                    f'Token refresh successful for user {user.email if user_id else "unknown"} '
                    f'from IP: {client_ip}, Processing time: {processing_time:.3f}s'
                )
                
                security_logger.info(
                    f'JWT_TOKEN_REFRESH_SUCCESS: '
                    f'user_id={user_id}, '
                    f'ip={client_ip}, '
                    f'processing_time={processing_time:.3f}s'
                )
                
                # Add metadata to response
                response.data['metadata'] = {
                    'refresh_time': int(time.time()),
                    'processing_time_ms': int(processing_time * 1000)
                }
                
            else:
                # Log failed refresh
                auth_logger.warning(
                    f'Token refresh failed for user {user.email if user_id else "unknown"} '
                    f'from IP: {client_ip}, Status: {response.status_code}, '
                    f'Processing time: {processing_time:.3f}s'
                )
                
                security_logger.warning(
                    f'JWT_TOKEN_REFRESH_FAILED: '
                    f'user_id={user_id}, '
                    f'ip={client_ip}, '
                    f'status={response.status_code}, '
                    f'processing_time={processing_time:.3f}s'
                )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log unexpected errors
            auth_logger.error(
                f'Token refresh error from IP: {client_ip}, '
                f'Error: {str(e)}, Processing time: {processing_time:.3f}s'
            )
            
            security_logger.error(
                f'JWT_TOKEN_REFRESH_ERROR: '
                f'ip={client_ip}, '
                f'error={str(e)}, '
                f'processing_time={processing_time:.3f}s'
            )
            
            return Response(
                {'error': 'Internal server error during token refresh'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip


@method_decorator(never_cache, name='dispatch')
class TokenStatusView(TokenRefreshView):
    """
    View to check token status and provide refresh recommendations.
    """
    
    def get(self, request, *args, **kwargs):
        """Get current token status."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'No valid token provided'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            
            current_time = time.time()
            exp_time = access_token.payload.get('exp')
            
            if not exp_time:
                return Response(
                    {'error': 'Invalid token format'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            time_until_expiry = exp_time - current_time
            expires_soon = time_until_expiry < 300  # 5 minutes
            
            return Response({
                'valid': True,
                'expires_at': exp_time,
                'expires_in_seconds': int(time_until_expiry),
                'expires_soon': expires_soon,
                'should_refresh': expires_soon,
                'current_time': int(current_time)
            })
            
        except TokenError:
            return Response(
                {'valid': False, 'expired': True, 'should_refresh': True}, 
                status=status.HTTP_401_UNAUTHORIZED
            )