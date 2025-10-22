"""
Health check endpoint for monitoring application status
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health_check(request):
    """
    Simple health check endpoint for monitoring.

    Returns JSON with application status and database connectivity.
    Useful for load balancers, monitoring systems, and uptime checks.

    Returns:
        200 OK if healthy
        500 Internal Server Error if unhealthy
    """
    checks = {
        'status': 'healthy',
        'database': 'unknown',
    }

    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                checks['database'] = 'ok'
            else:
                checks['database'] = 'error'
                checks['status'] = 'unhealthy'

    except Exception as e:
        checks['status'] = 'unhealthy'
        checks['database'] = 'error'
        checks['error'] = str(e)
        return JsonResponse(checks, status=500)

    return JsonResponse(checks)
