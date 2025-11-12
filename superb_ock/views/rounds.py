"""
Round management views.

Handles:
- Creating new rounds (NewRound)
- Viewing all rounds (RoundsOverview)
- Viewing individual round details (GolfRoundView)
"""
from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db import models
from django.db.models import Sum, Count, Q

from ..models import GolfCourse, GolfEvent, GolfRound, Hole, Player, Score
from .utils import jsonify
from ..utils.handicap import calculate_playing_handicap


class NewRound(View):
    """
    Create a new golf round.

    GET: Display form with courses, players, and events
    POST: Create round and scores for all players
    """

    template_name = "superb_ock/new_round/new_round.html"

    def get_context(self):
        """Build context for new round form."""
        courses = GolfCourse.objects.values()
        courses = jsonify(courses)

        players = Player.objects.order_by("first_name").values()
        players = jsonify(players)

        events = GolfEvent.objects.order_by("name").values()

        context = {
            "courses": courses,
            "players": players,
            "events": events,
        }
        return context

    def get(self, request):
        """Display new round form."""
        return render(request, self.template_name, context=self.get_context())

    def post(self, request):
        """
        Create new round with scores for all players.

        Sends notification and bulk creates all score objects.
        """
        course_id = request.POST.get("courseId")

        # Extract players from request data (avoids unnecessary dictionary creation)
        players = [
            {
                "id": request.POST.get(f"player_{x+1}"),
                "index": request.POST.get(f"player_{x+1}_index"),
            }
            for x in range(4)
            if request.POST.get(f"player_{x+1}")
        ]

        # Check if playing handicap (95%) should be used
        use_playing_handicap = request.POST.get("usePlayingHandicap") == "on"

        # Create the golf round
        golf_round = GolfRound.objects.create(
            event_id=request.POST.get("eventId"),
            date_started=timezone.now().date(),
            use_playing_handicap=use_playing_handicap
        )

        # Send notification to subscribed users
        from ..notifications import send_round_start_notification
        send_round_start_notification(golf_round)

        # Fetch all holes for the course in a single query, indexed by hole_number
        holes = {
            hole.hole_number: hole
            for hole in Hole.objects.filter(golf_course_id=course_id)
        }

        # Create Score objects efficiently
        score_objects = [
            Score(
                shots_taken=None,
                stableford=None,
                hole=holes.get(x + 1),  # Efficient lookup in the dictionary
                player_id=player["id"],
                golf_round_id=golf_round.pk,
                handicap_index=player["index"],
                sandy=False,
            )
            for player in players
            for x in range(18)
            if holes.get(x + 1)  # Ensures hole exists before creating a Score
        ]

        # Bulk create to reduce database hits
        Score.objects.bulk_create(score_objects)
        course = GolfCourse.objects.filter(id=course_id).get()

        player_objects = list(
            Player.objects.filter(id__in=[player["id"] for player in players]).values()
        )

        # Create a lookup dictionary for fast access
        player_index_lookup = {
            int(person["id"]): float(person["index"]) for person in players
        }

        # Update player objects with handicap calculations
        for player in player_objects:
            player_id = int(player["id"])
            if player_id in player_index_lookup:
                player["index"] = player_index_lookup[player_id]
                player["handicap"] = calculate_playing_handicap(
                    handicap_index=player["index"],
                    slope_rating=float(course.slope_rating),
                    course_rating=float(course.course_rating),
                    par=float(course.par),
                    use_playing_handicap=use_playing_handicap
                )

        context = {"course": course, "players": player_objects}

        # Return response
        return render(
            request, "superb_ock/new_round/round_created.html", context=context
        )


class RoundsOverview(View):
    """
    Display overview of all rounds with pagination.

    Groups rounds by event and course, showing player scores.
    Paginated at 10 events per page.
    """

    template_name = "superb_ock/rounds/overview.html"

    def convert_to_dict(self, d):
        """Recursively convert dict structure."""
        if isinstance(d, dict):
            return {k: self.convert_to_dict(v) for k, v in d.items()}
        return d

    def group_scores(self, data):
        """
        Group scores by event, course, round, and player.

        Returns nested dict structure for template rendering.
        """
        grouped = {}

        for entry in data:
            event = entry["golf_round__event__name"]
            course = f"{entry['hole__golf_course__name']} - {entry['hole__golf_course__tees']}{entry['golf_round_id']:05}"
            id = entry["golf_round_id"]
            player = f"{entry['player__first_name']} {entry['player__second_name']}"

            if event not in grouped:
                grouped[event] = {}
            if course not in grouped[event]:
                grouped[event][course] = {}
            if id not in grouped[event][course]:
                grouped[event][course][id] = {}
            if player not in grouped[event][course][id]:
                grouped[event][course][id][player] = {"shots_taken": 0, "stableford": 0}

            grouped[event][course][id][player]["shots_taken"] += (
                entry["shots_taken"] if entry["shots_taken"] else 0
            )
            grouped[event][course][id][player]["stableford"] += (
                entry["stableford"] if entry["stableford"] else 0
            )

        return self.convert_to_dict(grouped)

    def get(self, request):
        """Display paginated rounds overview."""
        scores = (
            Score.objects.all()
            .order_by("-golf_round__event__name", "golf_round_id", "player__first_name", "player__second_name")
            .values(
                "player__first_name",
                "player__second_name",
                "shots_taken",
                "stableford",
                "golf_round__event__name",
                "hole__golf_course__name",
                "hole__golf_course__tees",
                "golf_round_id",
            )
        )
        grouped_data = self.group_scores(scores)

        # Convert grouped_data dict to list of items for pagination
        # Each item is (event_name, event_rounds)
        rounds_list = list(grouped_data.items())

        # Paginate - show 10 events per page
        paginator = Paginator(rounds_list, 10)
        page_number = request.GET.get('page', 1)

        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)

        # Convert back to dict for template compatibility
        paginated_rounds = dict(page_obj.object_list)

        return render(request, self.template_name, context={
            "rounds": paginated_rounds,
            "page_obj": page_obj,
            "is_paginated": paginator.num_pages > 1
        })


class GolfRoundView(View):
    """
    Display detailed view of a single round.

    Shows:
    - All player scores by hole
    - Front/back nine totals
    - Stableford points
    - Highlights
    - Other concurrent rounds
    - Navigation to next/previous rounds
    """

    template_name = "superb_ock/rounds/round.html"

    def get(self, request, round_id):
        """Display round details."""
        scores = (
            Score.objects.filter(golf_round__id=round_id)
            .select_related()
            .order_by("player__first_name", "player__second_name")
            .values(
                "player_id",
                "shots_taken",
                "stableford",
                "player__first_name",
                "player__second_name",
                "hole__hole_number",
                "hole__par",
                "hole__yards",
                "hole__stroke_index",
                "golf_round__event_id",
                "handicap_index",
                "hole__golf_course__slope_rating",
                "hole__golf_course__course_rating",
                "hole__golf_course__par",
            )
        )

        # Get the current round's event ID for cross-round summary
        current_round = GolfRound.objects.get(id=round_id)
        event_id = current_round.event.pk

        # Get summary of other concurrent rounds in the same event (same day only)
        other_rounds_summary = (
            Score.objects.filter(
                golf_round__event_id=event_id,
                golf_round__date_started=current_round.date_started
            )
            .exclude(golf_round__id=round_id)
            .values("golf_round_id", "player__first_name", "player__second_name")
            .annotate(
                total_stableford=models.Sum("stableford"),
                total_shots=models.Sum("shots_taken"),
                holes_played=models.Count("id", filter=models.Q(shots_taken__isnull=False))
            )
            .order_by("golf_round_id", "-total_stableford")
        )

        # Group other rounds data
        other_rounds = {}
        for summary in other_rounds_summary:
            round_id_key = summary["golf_round_id"]
            if round_id_key not in other_rounds:
                other_rounds[round_id_key] = {
                    "players": [],
                    "max_holes_played": 0
                }
            other_rounds[round_id_key]["players"].append({
                "player": f"{summary['player__first_name']} {summary['player__second_name']}",
                "total_stableford": summary["total_stableford"] or 0,
                "total_shots": summary["total_shots"] or 0,
                "holes_played": summary["holes_played"]
            })
            # Track max holes played for this round
            other_rounds[round_id_key]["max_holes_played"] = max(
                other_rounds[round_id_key]["max_holes_played"],
                summary["holes_played"]
            )

        grouped_summary = {}
        for item in scores:
            player_full_name = f"{item['player__first_name']} {item['player__second_name']}"
            if player_full_name not in grouped_summary:
                grouped_summary[player_full_name] = {"total_shots": 0, "total_stableford": 0, "scores": []}
            grouped_summary[player_full_name]["total_shots"] += (
                item["shots_taken"] if item["shots_taken"] else 0
            )
            grouped_summary[player_full_name]["total_stableford"] += (
                item["stableford"] if item["stableford"] else 0
            )
            grouped_summary[player_full_name]["scores"].append(item)
        grouped_data = dict(grouped_summary)
        summary_data = {}
        for player, data in grouped_data.items():
            # Get handicap info from first score entry
            first_score = data['scores'][0] if data['scores'] else {}
            handicap_index = first_score.get('handicap_index', 0)
            slope_rating = first_score.get('hole__golf_course__slope_rating', 113)
            course_rating = first_score.get('hole__golf_course__course_rating', 72)
            course_par = first_score.get('hole__golf_course__par', 72)
            course_handicap = calculate_playing_handicap(
                handicap_index=handicap_index,
                slope_rating=slope_rating,
                course_rating=course_rating,
                par=course_par,
                use_playing_handicap=current_round.use_playing_handicap
            )

            summary_data[player] = {
                'front_nine': 0,
                'back_nine': 0,
                'total_shots': 0,
                'front_nine_stableford': 0,
                'back_nine_stableford': 0,
                'total_stableford': 0,
                'handicap_index': handicap_index,
                'course_handicap': course_handicap,
                'course_par': course_par,
                'played_holes_par': 0,  # Par for only the holes that have been played
            }
            for score in data.get('scores', []):
                if score['hole__hole_number'] < 10:
                    summary_data[player]['front_nine'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['total_shots'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['front_nine_stableford'] += score['stableford'] if score['stableford'] else 0
                    summary_data[player]['total_stableford'] += score['stableford'] if score['stableford'] else 0
                    # Only add to played holes par if the score has been entered
                    if score['shots_taken'] is not None:
                        summary_data[player]['played_holes_par'] += score['hole__par'] or 0
                else:
                    summary_data[player]['back_nine'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['total_shots'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['back_nine_stableford'] += score['stableford'] if score['stableford'] else 0
                    summary_data[player]['total_stableford'] += score['stableford'] if score['stableford'] else 0
                    # Only add to played holes par if the score has been entered
                    if score['shots_taken'] is not None:
                        summary_data[player]['played_holes_par'] += score['hole__par'] or 0

        # Get highlights for this round
        round_highlights = Score.objects.filter(
            golf_round__id=round_id
        ).prefetch_related(
            'highlight__previews'
        ).order_by(
            'player__first_name', 'player__second_name', 'hole__hole_number'
        ).exclude(
            highlight__isnull=True
        ).distinct()

        # Organize highlights by player and hole
        highlights_data = {}
        for score in round_highlights:
            if score.player and score.player.first_name and score.player.second_name:
                player_name = f"{score.player.first_name} {score.player.second_name}"
                hole_number = score.hole.hole_number if score.hole else 0

                if player_name not in highlights_data:
                    highlights_data[player_name] = {}
                if hole_number not in highlights_data[player_name]:
                    highlights_data[player_name][hole_number] = []

                for highlight in score.highlight.all():
                    highlights_data[player_name][hole_number].append({
                        'highlight': highlight,
                        'score': score
                    })

        # Get round info for display
        round_info = {
            'round': current_round,
            'event': current_round.event,
            'date': current_round.date_started,
        }

        # Get course info from first score if available
        first_score = scores.first()
        if first_score:
            course_data = Score.objects.filter(golf_round__id=round_id).select_related(
                'hole__golf_course'
            ).first()
            if course_data and course_data.hole and course_data.hole.golf_course:
                round_info.update({
                    'course': course_data.hole.golf_course,
                    'course_name': course_data.hole.golf_course.name,
                    'tees': course_data.hole.golf_course.tees,
                    'par': course_data.hole.golf_course.par,
                    'course_rating': course_data.hole.golf_course.course_rating,
                    'slope_rating': course_data.hole.golf_course.slope_rating,
                })

        # Get navigation data for next/previous rounds in the same event
        # Find all rounds in the same event, ordered by ID
        event_rounds = GolfRound.objects.filter(
            event_id=event_id
        ).order_by('id').values_list('id', flat=True)

        # Convert to list for easier manipulation
        round_ids = list(event_rounds)
        current_index = round_ids.index(round_id) if round_id in round_ids else -1

        # Determine next and previous round IDs
        next_round_id = None
        previous_round_id = None

        if current_index != -1:
            if current_index > 0:
                previous_round_id = round_ids[current_index - 1]
            if current_index < len(round_ids) - 1:
                next_round_id = round_ids[current_index + 1]

        # Get additional info for next/previous rounds
        navigation_info = {}
        if next_round_id:
            next_round = GolfRound.objects.get(id=next_round_id)
            navigation_info['next_round'] = {
                'id': next_round_id,
                'round_obj': next_round,
                'round_number': current_index + 2,  # Human-readable round number
                'total_rounds': len(round_ids)
            }

        if previous_round_id:
            previous_round = GolfRound.objects.get(id=previous_round_id)
            navigation_info['previous_round'] = {
                'id': previous_round_id,
                'round_obj': previous_round,
                'round_number': current_index,  # Human-readable round number
                'total_rounds': len(round_ids)
            }

        # Add current round info
        navigation_info['current_round'] = {
            'round_number': current_index + 1,
            'total_rounds': len(round_ids)
        }

        return render(
            request,
            self.template_name,
            context={
                "scores": grouped_data,
                "round_id": round_id,
                "summary": summary_data,
                "other_rounds": other_rounds,
                "highlights_data": highlights_data,
                "round_info": round_info,
                "navigation_info": navigation_info
                },
        )
