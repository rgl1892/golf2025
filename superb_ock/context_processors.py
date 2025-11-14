"""
Context processors for making variables available in all templates.
"""
from django.conf import settings


def static_version(request):
    """Add STATIC_VERSION to all template contexts for cache busting."""
    return {
        'STATIC_VERSION': settings.STATIC_VERSION
    }
