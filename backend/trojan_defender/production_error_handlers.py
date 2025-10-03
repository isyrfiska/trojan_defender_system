from django.http import JsonResponse
from django.conf import settings

def handle_400(request, exception=None):
    """
    Handle 400 Bad Request errors in production
    """
    return JsonResponse({
        'error': 'Bad request',
        'message': 'The request could not be understood by the server due to malformed syntax.',
        'status_code': 400
    }, status=400)

def handle_403(request, exception=None):
    """
    Handle 403 Forbidden errors in production
    """
    return JsonResponse({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource.',
        'status_code': 403
    }, status=403)

def handle_404(request, exception=None):
    """
    Handle 404 Not Found errors in production
    """
    return JsonResponse({
        'error': 'Not found',
        'message': 'The requested resource was not found on this server.',
        'status_code': 404
    }, status=404)

def handle_500(request):
    """
    Handle 500 Internal Server Error in production
    """
    return JsonResponse({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Our technical team has been notified.',
        'status_code': 500
    }, status=500)