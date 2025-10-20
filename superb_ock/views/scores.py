"""
Score editing views.

Handles editing individual hole scores for a golf round.
"""
from django.shortcuts import render, redirect
from django.views import View
from django.db import models

from ..models import Score


class EditScore(View):
    """
    Edit scores for a specific hole in a round.

    GET: Display score entry form with current totals
    POST: Update scores for all players on the hole
    """

    template_name = "superb_ock/rounds/edit_score.html"

    def get_context_data(self, round_id, hole_number):
        """
        Build context data for score editing form.

        Args:
            round_id: The golf round ID
            hole_number: The hole number being edited

        Returns:
            Dict containing scores per hole, player totals, and metadata
        """
        scores = (
            Score.objects.filter(golf_round=round_id)
            .order_by("player__first_name")
            .values(
                "shots_taken",
                "stableford",
                "id",
                "hole__hole_number",
                "hole__yards",
                "hole__par",
                "player__first_name",
                "player__second_name",
                "handicap_index",
                "sandy",
                "golf_round",
                "hole__stroke_index",
                "hole__golf_course__slope_rating",
                "hole__golf_course__course_rating",
                "hole__golf_course__par",
            )
        )

        scores_per_hole = [
            [score for score in scores if score["hole__hole_number"] == x + 1]
            for x in range(18)
        ]

        # Calculate current totals for each player
        player_totals = {}
        for score in scores:
            player_name = f"{score['player__first_name']} {score['player__second_name']}"
            if player_name not in player_totals:
                player_totals[player_name] = {
                    "total_shots": 0,
                    "total_stableford": 0,
                    "played_holes_par": 0,
                    "holes_played": 0
                }

            # Only count holes that have been played
            if score["shots_taken"] is not None:
                player_totals[player_name]["total_shots"] += score["shots_taken"]
                player_totals[player_name]["total_stableford"] += score["stableford"] or 0
                player_totals[player_name]["played_holes_par"] += score["hole__par"] or 0
                player_totals[player_name]["holes_played"] += 1

        context = {
            "scores_per_hole": scores_per_hole,
            "round_id": round_id,
            "hole_number": hole_number,
            "player_totals": player_totals,
        }
        return context

    def get(self, request, round_id, hole_number):
        """Display score editing form (requires authentication)."""
        if request.user.is_authenticated:
            return render(
                request,
                self.template_name,
                self.get_context_data(round_id, hole_number),
            )
        else:
            return redirect("golf_round", round_id=round_id)

    def post(self, request, round_id, hole_number):
        """
        Update scores for all players on this hole.

        Parses POST data, updates scores in database, and sends notifications.
        """
        post_data = request.POST

        formatted_data = {}

        # Temporary dict to hold player data
        players = {}

        for key in post_data:
            if key.startswith('shots_') or key.startswith('stable_'):
                # Get player ID from the key
                prefix, player_id_str = key.split('_')
                player_id = int(player_id_str)

                # Get the value and convert it from list to int
                value = int(post_data.getlist(key)[0])

                # Update the appropriate field
                if player_id not in players:
                    players[player_id] = {'shots': None, 'stable': None}
                if prefix == 'shots':
                    players[player_id]['shots'] = value
                elif prefix == 'stable':
                    players[player_id]['stable'] = value

        # Merge the player data into the final structure
        formatted_data.update(players)

        print(formatted_data)

        for score_id, points in formatted_data.items():
            Score.objects.filter(pk=score_id).update(
                shots_taken=points['shots'],
                stableford=points['stable']
            )

            # Send notification for completed hole
            try:
                from ..notifications import send_hole_completed_notification
                score = Score.objects.get(pk=score_id)
                if score.shots_taken is not None:  # Only notify if a score was actually entered
                    # Calculate player's total stableford points for the round
                    player_total = Score.objects.filter(
                        golf_round=score.golf_round,
                        player=score.player,
                        shots_taken__isnull=False
                    ).aggregate(total=models.Sum('stableford'))['total'] or 0

                    send_hole_completed_notification(score, player_total)
            except Exception as e:
                print(f"[NOTIFICATION] Error sending hole completed notification: {e}")

        return render(
            request, self.template_name, self.get_context_data(round_id, hole_number)
        )
