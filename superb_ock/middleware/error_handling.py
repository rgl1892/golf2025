"""
Error Handling Middleware

Provides comprehensive error handling and logging for the application.
Captures unhandled exceptions and provides user-friendly error pages.
"""

import logging
import traceback
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse

logger = logging.getLogger('superb_ock.errors')


class ErrorHandlingMiddleware:
    """
    Middleware for handling errors gracefully and logging them appropriately.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions that occur during request processing.
        """
        # Log the exception with full traceback
        logger.error(
            f"Unhandled exception: {str(exception)}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                'ip_address': self.get_client_ip(request),
            }
        )

        # In development, let Django's default error handling show detailed errors
        if settings.DEBUG:
            return None

        # In production, show user-friendly error pages
        if request.is_ajax() or request.content_type == 'application/json':
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'message': 'Please try again or contact support if the problem persists.'
            }, status=500)

        # Render custom error template
        return render(request, 'errors/500.html', {
            'error_id': self.generate_error_id(),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@example.com')
        }, status=500)

    def get_client_ip(self, request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def generate_error_id(self):
        """Generate a unique error ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]


class RequestLoggingMiddleware:
    """
    Middleware for logging all requests and responses.
    Useful for debugging and monitoring in production.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('superb_ock.requests')

    def __call__(self, request):
        # Log request
        if settings.DEBUG or getattr(settings, 'LOG_REQUESTS', False):
            self.logger.info(
                f"{request.method} {request.path}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                }
            )

        # Process request
        response = self.get_response(request)

        # Log response
        if settings.DEBUG or getattr(settings, 'LOG_REQUESTS', False):
            self.logger.info(
                f"{request.method} {request.path} -> {response.status_code}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                }
            )

        return response
