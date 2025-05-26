from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Avg
from .models import Score, GolfRound, Player, GolfCourse
from .serializers import ScoreSerializer, RoundSerializer, PlayerSerializer, CourseSerializer

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
    
    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        """Update multiple scores at once - useful for scorecard entry"""
        updates = request.data.get('updates', [])
        updated_scores = []
        
        for update in updates:
            score_id = update.get('id')
            if score_id:
                try:
                    score = Score.objects.get(id=score_id)
                    score.shots_taken = update.get('shots_taken', score.shots_taken)
                    score.stableford = update.get('stableford', score.stableford)
                    score.save()
                    updated_scores.append(ScoreSerializer(score).data)
                except Score.DoesNotExist:
                    continue
        
        return Response({'updated_scores': updated_scores})

class RoundViewSet(viewsets.ModelViewSet):
    queryset = GolfRound.objects.all()
    serializer_class = RoundSerializer

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = GolfCourse.objects.all()
    serializer_class = CourseSerializer

@api_view(['GET'])
def heatmap_data(request):
    """API endpoint for heatmap data"""
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
        for s in scores if s["avg_stableford"] is not None
    ]

    return Response(heatmap)

@api_view(['GET', 'POST'])
def round_scores(request, round_id):
    """Get or update scores for a specific round"""
    if request.method == 'GET':
        scores = Score.objects.filter(golf_round_id=round_id).select_related(
            'player', 'hole', 'hole__golf_course'
        )
        return Response(ScoreSerializer(scores, many=True).data)
    
    elif request.method == 'POST':
        # Handle score updates
        score_data = request.data
        updated_scores = []
        
        for score_update in score_data:
            score_id = score_update.get('id')
            if score_id:
                try:
                    score = Score.objects.get(id=score_id, golf_round_id=round_id)
                    serializer = ScoreSerializer(score, data=score_update, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        updated_scores.append(serializer.data)
                except Score.DoesNotExist:
                    continue
        
        return Response({'updated_scores': updated_scores})
