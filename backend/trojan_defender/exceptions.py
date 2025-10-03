"""
Custom exception classes for Trojan Defender application.
Provides structured error handling with proper logging and user-friendly messages.
"""

import logging
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError, DatabaseError

logger = logging.getLogger(__name__)


class TrojanDefenderException(Exception):
    """Base exception class for Trojan Defender application."""
    
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ScannerException(TrojanDefenderException):
    """Exception raised for scanner-related errors."""
    pass


class ThreatIntelligenceException(TrojanDefenderException):
    """Exception raised for threat intelligence API errors."""
    pass


class AuthenticationException(TrojanDefenderException):
    """Exception raised for authentication-related errors."""
    pass


class ValidationException(TrojanDefenderException):
    """Exception raised for validation errors."""
    pass


class RateLimitException(TrojanDefenderException):
    """Exception raised when rate limits are exceeded."""
    pass


class FileUploadException(TrojanDefenderException):
    """Exception raised for file upload errors."""
    pass


class ExternalAPIException(TrojanDefenderException):
    """Exception raised for external API communication errors."""
    pass


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides structured error responses
    and comprehensive logging.
    """
    # Get the standard error response
    response = exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception with context
    log_exception(exc, request, view)
    
    # Handle custom exceptions
    if isinstance(exc, TrojanDefenderException):
        custom_response_data = {
            'error': {
                'message': exc.message,
                'code': exc.error_code or 'UNKNOWN_ERROR',
                'details': exc.details,
                'timestamp': logger.handlers[0].formatter.formatTime(
                    logging.LogRecord('', 0, '', 0, '', (), None)
                ) if logger.handlers else None
            }
        }
        
        # Determine status code based on exception type
        if isinstance(exc, ValidationException):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, AuthenticationException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, RateLimitException):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, FileUploadException):
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        elif isinstance(exc, ExternalAPIException):
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
        return Response(custom_response_data, status=status_code)
    
    # Handle Django validation errors
    elif isinstance(exc, DjangoValidationError):
        custom_response_data = {
            'error': {
                'message': 'Validation error',
                'code': 'VALIDATION_ERROR',
                'details': {'validation_errors': exc.messages},
            }
        }
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle database errors
    elif isinstance(exc, IntegrityError):
        custom_response_data = {
            'error': {
                'message': 'Database integrity error',
                'code': 'INTEGRITY_ERROR',
                'details': {'database_error': str(exc)},
            }
        }
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, DatabaseError):
        custom_response_data = {
            'error': {
                'message': 'Database error occurred',
                'code': 'DATABASE_ERROR',
                'details': {},
            }
        }
        return Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Handle 404 errors
    elif isinstance(exc, Http404):
        custom_response_data = {
            'error': {
                'message': 'Resource not found',
                'code': 'NOT_FOUND',
                'details': {},
            }
        }
        return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
    
    # Enhance standard DRF error responses
    if response is not None:
        custom_response_data = {
            'error': {
                'message': get_error_message(response.data),
                'code': get_error_code(response.status_code),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data},
            }
        }
        response.data = custom_response_data
    
    return response


def log_exception(exc, request=None, view=None):
    """
    Log exception with comprehensive context information.
    """
    # Prepare context information
    context_info = {
        'exception_type': type(exc).__name__,
        'exception_message': str(exc),
    }
    
    if request:
        context_info.update({
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        })
    
    if view:
        context_info.update({
            'view_class': view.__class__.__name__,
            'view_action': getattr(view, 'action', None),
        })
    
    # Log based on exception severity
    if isinstance(exc, (TrojanDefenderException, DjangoValidationError)):
        logger.warning(
            f"Application exception: {exc}",
            extra=context_info,
            exc_info=False
        )
    elif isinstance(exc, (DatabaseError, IntegrityError)):
        logger.error(
            f"Database exception: {exc}",
            extra=context_info,
            exc_info=True
        )
    else:
        logger.error(
            f"Unhandled exception: {exc}",
            extra=context_info,
            exc_info=True
        )


def get_client_ip(request):
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_error_message(data):
    """
    Extract a user-friendly error message from response data.
    """
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        elif 'message' in data:
            return str(data['message'])
        elif 'error' in data:
            return str(data['error'])
        else:
            # Try to get the first error message from field errors
            for key, value in data.items():
                if isinstance(value, list) and value:
                    return f"{key}: {value[0]}"
            return "An error occurred"
    elif isinstance(data, list) and data:
        return str(data[0])
    else:
        return str(data) if data else "An error occurred"


def get_error_code(status_code):
    """
    Map HTTP status codes to error codes.
    """
    error_code_map = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        406: 'NOT_ACCEPTABLE',
        409: 'CONFLICT',
        410: 'GONE',
        413: 'REQUEST_ENTITY_TOO_LARGE',
        415: 'UNSUPPORTED_MEDIA_TYPE',
        422: 'UNPROCESSABLE_ENTITY',
        429: 'TOO_MANY_REQUESTS',
        500: 'INTERNAL_SERVER_ERROR',
        501: 'NOT_IMPLEMENTED',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
        504: 'GATEWAY_TIMEOUT',
    }
    return error_code_map.get(status_code, 'UNKNOWN_ERROR')