"""
Visualization views for statistics and data display.
"""
from django.shortcuts import render
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache for 5 minutes
class HeatMap(View):
    """
    Heatmap visualization view.

    Cached for 5 minutes to reduce computation overhead.
    """

    def get(self, request):
        """Display heatmap visualization."""
        return render(request, 'superb_ock/stats/heatmap.html')
