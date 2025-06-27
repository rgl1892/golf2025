from .models import GolfEvent

def tournaments(request):
    """Add all tournaments to template context"""
    return {
        'tournaments': GolfEvent.objects.exclude(name__icontains='practice').order_by('name')
    }