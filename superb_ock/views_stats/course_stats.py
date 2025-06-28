from django.shortcuts import render
from django.db.models import Avg, Sum, Count, Min, Max, Q, F, StdDev, Variance
from django.http import JsonResponse
from ..models import Player, Score, GolfRound, GolfCourse, Hole
import math
import statistics


def course_stats_overview(request):
    """Course statistics overview - optimized version"""
    
    # Get filter parameter
    round_type_filter = request.GET.get('filter', 'all')
    
    # Get all courses with their related data in bulk
    courses = GolfCourse.objects.prefetch_related('hole_set').order_by('name')
    
    # Get all scores data in one query with course info
    all_scores = Score.objects.select_related('hole__golf_course', 'player', 'golf_round').filter(
        hole__golf_course__isnull=False
    )
    
    # Apply round type filtering
    if round_type_filter == 'ocks':
        all_scores = all_scores.exclude(golf_round__event__name__icontains='practice')
    elif round_type_filter == 'practice':
        all_scores = all_scores.filter(golf_round__event__name__icontains='practice')
    
    # Group scores by course
    course_scores = {}
    for score in all_scores:
        course_id = score.hole.golf_course.id
        if course_id not in course_scores:
            course_scores[course_id] = []
        course_scores[course_id].append(score)
    
    # Calculate bulk stats for all courses
    course_basic_stats = {}
    for course_id, scores in course_scores.items():
        # Basic counts
        total_rounds = len(set(score.golf_round.id for score in scores if score.golf_round))
        total_holes_played = len(scores)
        
        # Skip courses with no rounds
        if total_rounds == 0:
            continue
            
        # Scoring averages
        valid_scores = [s.shots_taken for s in scores if s.shots_taken is not None]
        valid_stableford = [s.stableford for s in scores if s.stableford is not None]
        
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        avg_stableford = sum(valid_stableford) / len(valid_stableford) if valid_stableford else 0
        
        # Best performances
        best_single_hole = max(valid_stableford) if valid_stableford else 0
        
        # Player round totals for best individual round
        player_round_totals = {}
        for score in scores:
            if score.golf_round and score.player and score.stableford is not None:
                key = (score.golf_round.id, score.player.id)
                if key not in player_round_totals:
                    player_round_totals[key] = 0
                player_round_totals[key] += score.stableford
        
        best_round_score = max(player_round_totals.values()) if player_round_totals else 0
        unique_players = len(set(score.player.id for score in scores if score.player))
        
        course_basic_stats[course_id] = {
            'total_rounds': total_rounds,
            'total_holes_played': total_holes_played,
            'avg_score': avg_score,
            'avg_stableford': avg_stableford,
            'best_round_score': best_round_score,
            'best_single_hole': best_single_hole,
            'unique_players': unique_players,
            'scores': scores
        }
    
    # Calculate advanced metrics and build final stats
    course_stats = []
    for course in courses:
        if course.id not in course_basic_stats:
            continue  # Skip courses with no scoring data
            
        basic_stats = course_basic_stats[course.id]
        
        # Course layout info (already prefetched)
        holes = list(course.hole_set.all())
        total_par = sum(hole.par for hole in holes if hole.par)
        avg_hole_length = sum(hole.yards for hole in holes if hole.yards) / len(holes) if holes else 0
        
        # Calculate advanced metrics using the optimized function
        advanced_metrics = calculate_advanced_difficulty_metrics_optimized(basic_stats['scores'], holes)
        
        difficulty_score = round(basic_stats['avg_stableford'], 1)
        
        course_stats.append({
            'course': course,
            'total_rounds': basic_stats['total_rounds'],
            'total_holes_played': basic_stats['total_holes_played'],
            'avg_score': round(basic_stats['avg_score'], 1) if basic_stats['avg_score'] else 0,
            'avg_stableford': difficulty_score,
            'difficulty_rating': get_difficulty_rating(difficulty_score),
            'advanced_difficulty_rating': get_advanced_difficulty_rating(advanced_metrics['difficulty_rating']),
            'difficulty_score': advanced_metrics['difficulty_rating'],
            'consistency_index': advanced_metrics['consistency_index'],
            'scoring_distribution': advanced_metrics['scoring_distribution'],
            'handicap_correlation': advanced_metrics['handicap_correlation'],
            'hole_difficulty_variance': advanced_metrics['hole_difficulty_variance'],
            'stableford_std_dev': advanced_metrics['stableford_std_dev'],
            'avg_shots_over_par': advanced_metrics['avg_shots_over_par'],
            'best_round_score': basic_stats['best_round_score'],
            'best_single_hole': basic_stats['best_single_hole'],
            'unique_players': basic_stats['unique_players'],
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


def course_difficulty_analysis_api(request):
    """API endpoint for advanced course difficulty analysis"""
    courses = GolfCourse.objects.all().order_by('name')
    
    difficulty_analysis = []
    for course in courses:
        # Check if course has any scoring data
        sample_size = Score.objects.filter(hole__golf_course=course).count()
        if sample_size == 0:
            continue
            
        advanced_metrics = calculate_advanced_difficulty_metrics(course)
        
        # Add course metadata
        holes = Hole.objects.filter(golf_course=course)
        total_par = holes.aggregate(sum=Sum('par'))['sum'] or 0
        avg_hole_length = holes.aggregate(avg=Avg('yards'))['avg']
        
        difficulty_analysis.append({
            'course_id': course.id,
            'course_name': course.name,
            'country': course.country,
            'tees': course.tees,
            'official_slope_rating': course.slope_rating,
            'official_course_rating': course.course_rating,
            'total_par': total_par,
            'avg_hole_length': round(avg_hole_length) if avg_hole_length else 0,
            'calculated_difficulty_rating': advanced_metrics['difficulty_rating'],
            'difficulty_category': get_advanced_difficulty_rating(advanced_metrics['difficulty_rating']),
            'consistency_index': advanced_metrics['consistency_index'],
            'avg_stableford': advanced_metrics['avg_stableford'],
            'stableford_std_dev': advanced_metrics['stableford_std_dev'],
            'avg_shots_over_par': advanced_metrics['avg_shots_over_par'],
            'scoring_distribution': advanced_metrics['scoring_distribution'],
            'handicap_correlation': advanced_metrics['handicap_correlation'],
            'hole_difficulty_variance': advanced_metrics['hole_difficulty_variance'],
            'sample_size': sample_size
        })
    
    # Sort by difficulty rating (hardest first)
    difficulty_analysis.sort(key=lambda x: x['calculated_difficulty_rating'], reverse=True)
    
    return JsonResponse({
        'difficulty_analysis': difficulty_analysis,
        'methodology': {
            'difficulty_rating': 'Calculated 0-100 scale based on average stableford scores and score variance',
            'consistency_index': 'How predictable the course plays (100 = very consistent, 0 = very inconsistent)',
            'handicap_correlation': 'Correlation between player handicap and performance (-1 to 1)',
            'hole_difficulty_variance': 'Standard deviation of individual hole difficulties',
            'scoring_distribution': 'Percentage breakdown of excellent/good/poor scoring rounds'
        }
    })


def calculate_advanced_difficulty_metrics_optimized(scores, holes):
    """Optimized version that works with pre-loaded data"""
    if not scores:
        return {
            'difficulty_rating': 0,
            'consistency_index': 0,
            'scoring_distribution': {'excellent_pct': 0, 'good_pct': 0, 'poor_pct': 0},
            'handicap_correlation': 0,
            'hole_difficulty_variance': 0,
            'avg_stableford': 0,
            'stableford_std_dev': 0,
            'avg_shots_over_par': 0
        }
    
    # 1. Scoring relative to par analysis
    scores_vs_par = []
    stableford_scores = []
    handicap_indices = []
    
    # Create hole par lookup
    hole_par_lookup = {hole.id: hole.par for hole in holes if hole.par}
    
    for score in scores:
        if (score.shots_taken is not None and score.stableford is not None and 
            score.hole and score.hole.id in hole_par_lookup):
            hole_par = hole_par_lookup[score.hole.id]
            shots_over_par = score.shots_taken - hole_par
            scores_vs_par.append(shots_over_par)
            stableford_scores.append(score.stableford)
            handicap_indices.append(score.handicap_index)
    
    # 2. Statistical measures
    avg_stableford = statistics.mean(stableford_scores) if stableford_scores else 0
    stableford_std = statistics.stdev(stableford_scores) if len(stableford_scores) > 1 else 0
    avg_shots_over_par = statistics.mean(scores_vs_par) if scores_vs_par else 0
    
    # 3. Difficulty Rating (0-100 scale)
    base_difficulty = max(0, (2.0 - avg_stableford) * 25)
    variance_penalty = min(25, stableford_std * 10)
    difficulty_rating = min(100, base_difficulty + variance_penalty)
    
    # 4. Consistency Index
    consistency_index = max(0, 100 - (stableford_std * 40)) if stableford_std else 100
    
    # 5. Scoring Distribution Analysis
    excellent_rounds = len([s for s in stableford_scores if s >= 3.0])
    good_rounds = len([s for s in stableford_scores if 2.0 <= s < 3.0])
    poor_rounds = len([s for s in stableford_scores if s < 2.0])
    total_scores = len(stableford_scores)
    
    scoring_distribution = {
        'excellent_pct': round((excellent_rounds / total_scores * 100), 1) if total_scores else 0,
        'good_pct': round((good_rounds / total_scores * 100), 1) if total_scores else 0,
        'poor_pct': round((poor_rounds / total_scores * 100), 1) if total_scores else 0
    }
    
    # 6. Handicap Correlation
    handicap_correlation = 0
    if len(handicap_indices) > 5 and len(set(handicap_indices)) > 2:
        try:
            correlation_data = list(zip(handicap_indices, stableford_scores))
            if correlation_data:
                n = len(correlation_data)
                sum_hcp = sum(h for h, s in correlation_data)
                sum_stableford = sum(s for h, s in correlation_data)
                sum_hcp_sq = sum(h*h for h, s in correlation_data)
                sum_stableford_sq = sum(s*s for h, s in correlation_data)
                sum_hcp_stableford = sum(h*s for h, s in correlation_data)
                
                numerator = n * sum_hcp_stableford - sum_hcp * sum_stableford
                denominator = math.sqrt((n * sum_hcp_sq - sum_hcp**2) * (n * sum_stableford_sq - sum_stableford**2))
                
                if denominator != 0:
                    handicap_correlation = round(numerator / denominator, 3)
        except:
            handicap_correlation = 0
    
    # 7. Hole Difficulty Variance
    hole_difficulties = []
    hole_stableford_lookup = {}
    
    # Group scores by hole
    for score in scores:
        if score.hole and score.stableford is not None:
            hole_id = score.hole.id
            if hole_id not in hole_stableford_lookup:
                hole_stableford_lookup[hole_id] = []
            hole_stableford_lookup[hole_id].append(score.stableford)
    
    # Calculate average for each hole
    for hole_scores in hole_stableford_lookup.values():
        if hole_scores:
            hole_avg = statistics.mean(hole_scores)
            hole_difficulties.append(hole_avg)
    
    hole_difficulty_variance = statistics.stdev(hole_difficulties) if len(hole_difficulties) > 1 else 0
    
    return {
        'difficulty_rating': round(difficulty_rating, 1),
        'consistency_index': round(consistency_index, 1),
        'scoring_distribution': scoring_distribution,
        'handicap_correlation': handicap_correlation,
        'hole_difficulty_variance': round(hole_difficulty_variance, 3),
        'avg_stableford': round(avg_stableford, 2),
        'stableford_std_dev': round(stableford_std, 2),
        'avg_shots_over_par': round(avg_shots_over_par, 2)
    }


def calculate_advanced_difficulty_metrics(course):
    """Calculate comprehensive difficulty metrics for a course"""
    scores = Score.objects.filter(hole__golf_course=course)
    holes = Hole.objects.filter(golf_course=course)
    
    if not scores.exists():
        return {
            'difficulty_rating': 0,
            'consistency_index': 0,
            'scoring_distribution': {'excellent_pct': 0, 'good_pct': 0, 'poor_pct': 0},
            'handicap_correlation': 0,
            'hole_difficulty_variance': 0,
            'avg_stableford': 0,
            'stableford_std_dev': 0,
            'avg_shots_over_par': 0
        }
    
    # 1. Scoring relative to par analysis
    scores_vs_par = []
    stableford_scores = []
    handicap_indices = []
    
    for score in scores.filter(shots_taken__isnull=False, stableford__isnull=False, hole__isnull=False):
        if score.hole and score.hole.par and score.shots_taken is not None:
            hole_par = score.hole.par
            shots_over_par = score.shots_taken - hole_par
            scores_vs_par.append(shots_over_par)
            stableford_scores.append(score.stableford)
            handicap_indices.append(score.handicap_index)
    
    # 2. Statistical measures
    avg_stableford = statistics.mean(stableford_scores) if stableford_scores else 0
    stableford_std = statistics.stdev(stableford_scores) if len(stableford_scores) > 1 else 0
    avg_shots_over_par = statistics.mean(scores_vs_par) if scores_vs_par else 0
    
    # 3. Difficulty Rating (0-100 scale)
    # Lower stableford = harder course
    # Adjust for score variance (inconsistent courses are harder)
    base_difficulty = max(0, (2.0 - avg_stableford) * 25)  # 0-50 range
    variance_penalty = min(25, stableford_std * 10)  # 0-25 range  
    difficulty_rating = min(100, base_difficulty + variance_penalty)
    
    # 4. Consistency Index (how predictable the course plays)
    consistency_index = max(0, 100 - (stableford_std * 40)) if stableford_std else 100
    
    # 5. Scoring Distribution Analysis
    excellent_rounds = len([s for s in stableford_scores if s >= 3.0])  # 3+ stableford avg
    good_rounds = len([s for s in stableford_scores if 2.0 <= s < 3.0])
    poor_rounds = len([s for s in stableford_scores if s < 2.0])
    total_scores = len(stableford_scores)
    
    scoring_distribution = {
        'excellent_pct': round((excellent_rounds / total_scores * 100), 1) if total_scores else 0,
        'good_pct': round((good_rounds / total_scores * 100), 1) if total_scores else 0,
        'poor_pct': round((poor_rounds / total_scores * 100), 1) if total_scores else 0
    }
    
    # 6. Handicap Correlation (do better players perform relatively better?)
    handicap_correlation = 0
    if len(handicap_indices) > 5 and len(set(handicap_indices)) > 2:
        try:
            # Calculate correlation between handicap and performance
            correlation_data = list(zip(handicap_indices, stableford_scores))
            if correlation_data:
                n = len(correlation_data)
                sum_hcp = sum(h for h, s in correlation_data)
                sum_stableford = sum(s for h, s in correlation_data)
                sum_hcp_sq = sum(h*h for h, s in correlation_data)
                sum_stableford_sq = sum(s*s for h, s in correlation_data)
                sum_hcp_stableford = sum(h*s for h, s in correlation_data)
                
                numerator = n * sum_hcp_stableford - sum_hcp * sum_stableford
                denominator = math.sqrt((n * sum_hcp_sq - sum_hcp**2) * (n * sum_stableford_sq - sum_stableford**2))
                
                if denominator != 0:
                    handicap_correlation = round(numerator / denominator, 3)
        except:
            handicap_correlation = 0
    
    # 7. Hole Difficulty Variance
    hole_difficulties = []
    for hole in holes:
        hole_scores = scores.filter(hole=hole, stableford__isnull=False)
        if hole_scores.exists():
            hole_avg_stableford = hole_scores.aggregate(avg=Avg('stableford'))['avg']
            hole_difficulties.append(hole_avg_stableford)
    
    hole_difficulty_variance = statistics.stdev(hole_difficulties) if len(hole_difficulties) > 1 else 0
    
    return {
        'difficulty_rating': round(difficulty_rating, 1),
        'consistency_index': round(consistency_index, 1),
        'scoring_distribution': scoring_distribution,
        'handicap_correlation': handicap_correlation,
        'hole_difficulty_variance': round(hole_difficulty_variance, 3),
        'avg_stableford': round(avg_stableford, 2),
        'stableford_std_dev': round(stableford_std, 2),
        'avg_shots_over_par': round(avg_shots_over_par, 2)
    }


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


def get_advanced_difficulty_rating(difficulty_score):
    """Convert numerical difficulty rating to descriptive category"""
    if difficulty_score >= 80:
        return "Extremely Hard"
    elif difficulty_score >= 65:
        return "Very Hard"
    elif difficulty_score >= 50:
        return "Hard"
    elif difficulty_score >= 35:
        return "Moderate"
    elif difficulty_score >= 20:
        return "Moderate-Easy"
    else:
        return "Easy"


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