from django.shortcuts import render
from django.db.models import Avg, Sum, Count, Min, Max, Q, F
from django.http import JsonResponse
from ..models import Player, Score, GolfRound, GolfCourse, Hole


def course_stats_overview(request):
    """Course statistics overview"""
    
    courses = GolfCourse.objects.all().order_by('name')
    
    course_stats = []
    for course in courses:
        scores = Score.objects.filter(hole__golf_course=course)
        holes = Hole.objects.filter(golf_course=course)
        
        # Basic stats
        total_rounds = scores.values('golf_round').distinct().count()
        total_holes_played = scores.count()
        
        # Scoring stats
        avg_score = scores.filter(shots_taken__isnull=False).aggregate(avg=Avg('shots_taken'))['avg']
        avg_stableford = scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
        
        # Course difficulty (lower stableford = harder)
        difficulty_score = round(avg_stableford, 1) if avg_stableford else 0
        
        # Best performances on this course
        best_round_score = scores.values('golf_round').annotate(
            total_stableford=Sum('stableford')
        ).order_by('-total_stableford').first()
        
        best_single_hole = scores.filter(stableford__isnull=False).aggregate(max=Max('stableford'))['max']
        
        # Player variety
        unique_players = scores.values('player').distinct().count()
        
        # Course layout info
        total_par = holes.aggregate(sum=Sum('par'))['sum'] or 0
        avg_hole_length = holes.aggregate(avg=Avg('yards'))['avg']
        
        course_stats.append({
            'course': course,
            'total_rounds': total_rounds,
            'total_holes_played': total_holes_played,
            'avg_score': round(avg_score, 1) if avg_score else 0,
            'avg_stableford': difficulty_score,
            'difficulty_rating': get_difficulty_rating(difficulty_score),
            'best_round_score': best_round_score['total_stableford'] if best_round_score else 0,
            'best_single_hole': best_single_hole or 0,
            'unique_players': unique_players,
            'total_par': total_par,
            'avg_hole_length': round(avg_hole_length) if avg_hole_length else 0,
        })
    
    context = {
        'course_stats': course_stats
    }
    
    return render(request, 'superb_ock/stats/course_stats.html', context)


def course_detail_stats(request, course_id):
    """Detailed stats for individual course"""
    
    course = GolfCourse.objects.get(id=course_id)
    holes = Hole.objects.filter(golf_course=course).order_by('hole_number')
    scores = Score.objects.filter(hole__golf_course=course).select_related('player', 'golf_round')
    
    # Hole-by-hole stats
    hole_stats = []
    for hole in holes:
        hole_scores = scores.filter(hole=hole)
        
        if hole_scores.exists():
            avg_score = hole_scores.filter(shots_taken__isnull=False).aggregate(avg=Avg('shots_taken'))['avg']
            avg_stableford = hole_scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
            
            # Performance distribution
            eagles = hole_scores.filter(shots_taken__lt=hole.par - 1).count()
            birdies = hole_scores.filter(shots_taken=hole.par - 1).count()
            pars = hole_scores.filter(shots_taken=hole.par).count()
            bogeys = hole_scores.filter(shots_taken=hole.par + 1).count()
            double_bogeys_plus = hole_scores.filter(shots_taken__gt=hole.par + 1).count()
            
            hole_stats.append({
                'hole': hole,
                'times_played': hole_scores.count(),
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'avg_stableford': round(avg_stableford, 1) if avg_stableford else 0,
                'eagles': eagles,
                'birdies': birdies,
                'pars': pars,
                'bogeys': bogeys,
                'double_bogeys_plus': double_bogeys_plus,
                'difficulty_index': calculate_hole_difficulty(avg_stableford, hole.par)
            })
    
    # Round performance on this course
    round_stats = {}
    for score in scores:
        round_id = score.golf_round.id
        if round_id not in round_stats:
            round_stats[round_id] = {
                'round': score.golf_round,
                'players': {},
                'course_record': 0
            }
        
        player_name = f"{score.player.first_name} {score.player.second_name}"
        if player_name not in round_stats[round_id]['players']:
            round_stats[round_id]['players'][player_name] = {
                'player': score.player,
                'total_shots': 0,
                'total_stableford': 0,
                'holes_played': 0
            }
        
        if score.shots_taken:
            round_stats[round_id]['players'][player_name]['total_shots'] += score.shots_taken
            round_stats[round_id]['players'][player_name]['holes_played'] += 1
        if score.stableford:
            round_stats[round_id]['players'][player_name]['total_stableford'] += score.stableford
    
    # Find course record
    course_record = 0
    course_record_holder = None
    for round_data in round_stats.values():
        for player_data in round_data['players'].values():
            if player_data['total_stableford'] > course_record:
                course_record = player_data['total_stableford']
                course_record_holder = player_data['player']
    
    # Player performance rankings on this course
    player_rankings = {}
    for score in scores:
        player_name = f"{score.player.first_name} {score.player.second_name}"
        if player_name not in player_rankings:
            player_rankings[player_name] = {
                'player': score.player,
                'rounds_played': 0,
                'total_stableford': 0,
                'avg_stableford': 0,
                'best_round': 0
            }
    
    # Calculate player averages
    for player_name in player_rankings:
        player_scores = scores.filter(player=player_rankings[player_name]['player'])
        rounds_played = player_scores.values('golf_round').distinct().count()
        total_stableford = player_scores.filter(stableford__isnull=False).aggregate(sum=Sum('stableford'))['sum']
        avg_stableford = player_scores.filter(stableford__isnull=False).aggregate(avg=Avg('stableford'))['avg']
        
        # Find best round for this player on this course
        best_round = 0
        for round_data in round_stats.values():
            if player_name in round_data['players']:
                best_round = max(best_round, round_data['players'][player_name]['total_stableford'])
        
        player_rankings[player_name].update({
            'rounds_played': rounds_played,
            'total_stableford': total_stableford or 0,
            'avg_stableford': round(avg_stableford, 1) if avg_stableford else 0,
            'best_round': best_round
        })
    
    # Sort by average stableford descending
    sorted_player_rankings = sorted(player_rankings.values(), key=lambda x: x['avg_stableford'], reverse=True)
    
    context = {
        'course': course,
        'hole_stats': hole_stats,
        'round_stats': list(round_stats.values()),
        'course_record': course_record,
        'course_record_holder': course_record_holder,
        'player_rankings': sorted_player_rankings,
    }
    
    return render(request, 'superb_ock/stats/course_detail.html', context)


def get_difficulty_rating(avg_stableford):
    """Convert average stableford to difficulty rating"""
    if avg_stableford >= 2.5:
        return "Easy"
    elif avg_stableford >= 2.0:
        return "Moderate"
    elif avg_stableford >= 1.5:
        return "Hard"
    else:
        return "Very Hard"


def calculate_hole_difficulty(avg_stableford, par):
    """Calculate hole difficulty index"""
    if not avg_stableford:
        return "Unknown"
    
    if avg_stableford >= 2.5:
        return "Easy"
    elif avg_stableford >= 2.0:
        return "Moderate"
    elif avg_stableford >= 1.5:
        return "Hard"
    else:
        return "Very Hard"