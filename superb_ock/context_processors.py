"""
Context processors for superb_ock application.
Makes additional variables available to all templates.
"""

import subprocess
from django.conf import settings
from .models import GolfEvent


def tournaments(request):
    """Add all tournaments to template context"""
    return {
        'tournaments': GolfEvent.objects.exclude(name__icontains='practice').order_by('name')
    }


def git_version(request):
    """
    Add git commit hash to templates for cache busting.

    Returns a short git hash that can be used as a version parameter
    for static files to ensure browsers load updated files.

    Usage in templates:
        <link href="{% static 'css/styles.css' %}?v={{ GIT_VERSION }}" rel="stylesheet">
    """
    try:
        # Get short git commit hash
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=settings.BASE_DIR,
            stderr=subprocess.DEVNULL
        ).decode('ascii').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback if git is not available or not a git repo
        git_hash = 'dev'

    return {
        'GIT_VERSION': git_hash,
        'DEBUG': settings.DEBUG,
    }


def static_version(request):
    """Add STATIC_VERSION to all template contexts for cache busting."""
    return {
        'STATIC_VERSION': settings.STATIC_VERSION
    }
