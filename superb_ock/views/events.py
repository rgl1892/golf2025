"""
Event management and leaderboard views.

Handles event-level views including leaderboards and cumulative scoring charts.
"""
import json
from django.shortcuts import render
from django.views import View

from ..models import GolfEvent, Score


class EventView(View):
    """
    Display event leaderboard with cumulative scoring chart.

    Shows:
    - Full event leaderboard with all rounds
    - Cumulative scoring progression chart
    - Course breakdown for each round
    - Scoring format-specific counting rounds
    """

    template_name = 'superb_ock/events/overview.html'

    def get(self, request, event_id):
        """Display event leaderboard and cumulative chart."""
        # Use LeaderboardBuilder service to generate leaderboard
        from ..services import LeaderboardBuilder

        builder = LeaderboardBuilder(event_id)
        entries = builder.build()

        # Convert to template-compatible format
        cleaned_leaderboard = builder.to_dict_format(entries)
        courses = builder.get_courses_list(entries)

        # Get round numbers for display
        round_numbers = sorted(set(r['num'] for entry in entries for r in entry.rounds if r.get('num')))

        # Generate cumulative data for chart
        cumulative_data = self.generate_cumulative_data(cleaned_leaderboard, round_numbers)

        # Calculate max holes for chart (usually 54 holes for 3 counting rounds)
        max_holes = max([len(player['data']) for player in cumulative_data]) if cumulative_data else 0
        hole_labels = list(range(1, max_holes + 1))

        context = {
            'leaderboard': cleaned_leaderboard,
            'round_numbers': round_numbers,
            'courses': courses,
            'cumulative_data': json.dumps(cumulative_data),
            'hole_labels_json': json.dumps(hole_labels),
            'max_holes': max_holes
        }

        return render(request, self.template_name, context=context)

    def generate_cumulative_data(self, leaderboard, round_numbers):
        """
        Generate cumulative scoring data for chart progression.

        Calculates hole-by-hole cumulative totals for each player based on
        the event's scoring format (best 3 of 5, last round counts, etc.).

        Args:
            leaderboard: List of player leaderboard entries
            round_numbers: List of round IDs in the event

        Returns:
            List of dicts with player name, hole-by-hole data, and final total
        """
        cumulative_data = []

        # Get event scoring format
        event_id = self.kwargs.get('event_id')
        event = GolfEvent.objects.get(id=event_id)
        scoring_format = event.scoring

        # Get all hole-by-hole scores for this event
        all_hole_scores = Score.objects.filter(
            golf_round__event=event_id
        ).select_related('player', 'golf_round', 'hole').order_by(
            'golf_round_id', 'hole__hole_number'
        )

        # Group scores by player and round
        player_round_scores = {}
        for score in all_hole_scores:
            player_name = f"{score.player.first_name} {score.player.second_name}"
            if player_name not in player_round_scores:
                player_round_scores[player_name] = {}
            if score.golf_round_id not in player_round_scores[player_name]:
                player_round_scores[player_name][score.golf_round_id] = []

            player_round_scores[player_name][score.golf_round_id].append({
                'hole': score.hole.hole_number,
                'stableford': score.stableford or 0
            })

        # Calculate round totals and determine counting rounds for each player
        for player_data in leaderboard:
            player_name = player_data['player']
            rounds = player_data['rounds']

            # Determine counting rounds based on scoring format
            valid_rounds = [r for r in rounds if r.get('total') is not None]

            if scoring_format == "best_three_of_five":
                # Best 3 rounds overall
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            elif scoring_format == "best_last_rounds_counts":
                # Best 2 of first 4 rounds + last round counts
                if len(valid_rounds) >= 3:
                    # Sort by round ID to get chronological order
                    sorted_rounds = sorted(valid_rounds, key=lambda x: x['num'])
                    last_round = sorted_rounds[-1]  # Last round always counts
                    first_rounds = sorted_rounds[:-1]  # All except last

                    # Get first 4 rounds (excluding the last round)
                    first_four_rounds = first_rounds[:4]  # Take only first 4

                    # Best 2 of the first 4 rounds
                    best_first_two = sorted(first_four_rounds, key=lambda x: x['total'], reverse=True)[:2]

                    counting_rounds = best_first_two + [last_round]
                    counting_round_ids = [r['num'] for r in counting_rounds]
                else:
                    # Not enough rounds, use all available
                    counting_round_ids = [r['num'] for r in valid_rounds]
            else:
                # Default to best 3
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]

            if player_name not in player_round_scores:
                continue

            # Get hole-by-hole data for counting rounds only, in chronological order
            all_counting_holes = []
            # Sort counting round IDs chronologically (by round ID)
            counting_round_ids_sorted = sorted(counting_round_ids)

            for round_id in counting_round_ids_sorted:
                if round_id in player_round_scores[player_name]:
                    round_holes = player_round_scores[player_name][round_id]
                    # Sort holes within each round (1-18)
                    round_holes.sort(key=lambda x: x['hole'])
                    # Add round_id to each hole for reference
                    for hole in round_holes:
                        hole['round_id'] = round_id
                    all_counting_holes.extend(round_holes)

            # Build cumulative progression by re-indexed hole position
            player_cumulative = []
            cumulative_total = 0

            for i, hole_data in enumerate(all_counting_holes):
                cumulative_total += hole_data['stableford']

                player_cumulative.append({
                    'hole_number': i + 1,  # Re-indexed position (1, 2, 3, ...)
                    'actual_hole': hole_data['hole'],  # Original hole number (1-18)
                    'round_id': hole_data['round_id'],  # Which round this hole is from
                    'hole_score': hole_data['stableford'],
                    'cumulative': cumulative_total
                })

            cumulative_data.append({
                'player': player_name,
                'data': player_cumulative,
                'final_total': cumulative_total
            })

        return cumulative_data
