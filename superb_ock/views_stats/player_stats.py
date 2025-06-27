from django.shortcuts import render
from django.db.models import Avg, Sum, Count, Min, Max, Q, F
from django.http import JsonResponse
from ..models import Player, Score, GolfRound, GolfCourse


def player_stats_overview(request):
    """Individual player statistics overview"""
    
    players = Player.objects.all().order_by('first_name')
    
    player_stats = []
    for player in players:
        scores = Score.objects.filter(player=player)
        
        # Basic stats
        total_rounds = scores.values('golf_round').distinct().count()
        total_holes = scores.count()
        
        # Scoring stats
        avg_score = scores.filter(shots_taken__isnull=False).aggregate(avg=Avg('shots_taken'))['avg']
        avg_stableford = scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
        total_stableford = scores.filter(stableford__isnull=False).aggregate(sum=Sum('stableford'))['sum']
        
        # Best performances
        best_hole_score = scores.filter(shots_taken__isnull=False).aggregate(min=Min('shots_taken'))['min']
        best_stableford_hole = scores.filter(stableford__isnull=False).aggregate(max=Max('stableford'))['max']
        
        # Special achievements
        eagles = scores.filter(shots_taken__lt=F('hole__par') - 1).count() if scores.exists() else 0
        birdies = scores.filter(shots_taken=F('hole__par') - 1).count() if scores.exists() else 0
        pars = scores.filter(shots_taken=F('hole__par')).count() if scores.exists() else 0
        sandies = scores.filter(sandy=True).count()
        
        # Course variety
        courses_played = scores.values('hole__golf_course').distinct().count()
        
        player_stats.append({
            'player': player,
            'total_rounds': total_rounds,
            'total_holes': total_holes,
            'avg_score': round(avg_score, 1) if avg_score else 0,
            'avg_stableford': round(avg_stableford, 1) if avg_stableford else 0,
            'total_stableford': total_stableford or 0,
            'best_hole_score': best_hole_score,
            'best_stableford_hole': best_stableford_hole,
            'eagles': eagles,
            'birdies': birdies,
            'pars': pars,
            'sandies': sandies,
            'courses_played': courses_played,
        })
    
    context = {
        'player_stats': player_stats
    }
    
    return render(request, 'superb_ock/stats/player_stats.html', context)


def player_detail_stats(request, player_id):
    """Detailed stats for individual player"""
    
    player = Player.objects.get(id=player_id)
    scores = Score.objects.filter(player=player).select_related('hole__golf_course', 'golf_round')
    
    # Round-by-round performance
    rounds = {}
    for score in scores:
        round_id = score.golf_round.id
        if round_id not in rounds:
            rounds[round_id] = {
                'round': score.golf_round,
                'course': score.hole.golf_course.name,
                'scores': [],
                'total_shots': 0,
                'total_stableford': 0,
                'holes_played': 0
            }
        
        rounds[round_id]['scores'].append(score)
        if score.shots_taken:
            rounds[round_id]['total_shots'] += score.shots_taken
            rounds[round_id]['holes_played'] += 1
        if score.stableford:
            rounds[round_id]['total_stableford'] += score.stableford
    
    # Course performance
    course_performance = {}
    for score in scores:
        course_name = score.hole.golf_course.name
        if course_name not in course_performance:
            course_performance[course_name] = {
                'course': score.hole.golf_course,
                'rounds_played': 0,
                'avg_score': 0,
                'avg_stableford': 0,
                'best_round': None,
            }
    
    # Calculate course averages
    for course_name in course_performance:
        course_scores = scores.filter(hole__golf_course__name=course_name)
        course_performance[course_name]['rounds_played'] = course_scores.values('golf_round').distinct().count()
        
        avg_score = course_scores.filter(shots_taken__isnull=False).aggregate(avg=Avg('shots_taken'))['avg']
        avg_stableford = course_scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
        
        course_performance[course_name]['avg_score'] = round(avg_score, 1) if avg_score else 0
        course_performance[course_name]['avg_stableford'] = round(avg_stableford, 1) if avg_stableford else 0
    
    # Hole-by-hole performance (1-18)
    hole_performance = []
    for hole_num in range(1, 19):
        hole_scores = scores.filter(hole__hole_number=hole_num)
        
        if hole_scores.exists():
            avg_score = hole_scores.filter(shots_taken__isnull=False).aggregate(avg=Avg('shots_taken'))['avg']
            avg_stableford = hole_scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
            times_played = hole_scores.count()
            
            hole_performance.append({
                'hole_number': hole_num,
                'times_played': times_played,
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'avg_stableford': round(avg_stableford, 1) if avg_stableford else 0,
            })
    
    context = {
        'player': player,
        'rounds': list(rounds.values()),
        'course_performance': list(course_performance.values()),
        'hole_performance': hole_performance,
    }
    
    return render(request, 'superb_ock/stats/player_detail.html', context)