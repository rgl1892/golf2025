from ..models import *
from django.http import JsonResponse
from django.db.models import Avg

def heatmap_data(request):
    """
    Returns a JSON response containing the average stableford scores for each player and hole.
    """
    scores = (
        Score.objects
        .select_related('player', 'hole')
        .values('player__first_name', 'player__second_name', 'hole__hole_number')
        .annotate(avg_stableford=Avg('stableford'))
        .order_by('player__second_name', 'hole__hole_number')
    )

    heatmap = [
        {
            "player": f"{s['player__first_name']} {s['player__second_name'][0]}",
            "hole": s["hole__hole_number"],
            "stableford": s["avg_stableford"]
        }
        for s in scores
    ]

    return JsonResponse(heatmap, safe=False)