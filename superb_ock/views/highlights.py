"""
Highlight video gallery views.

Handles displaying video highlights organized by player and round.
"""
from django.shortcuts import render
from django.views import View

from ..models import Highlight, Score


class HighlightsView(View):
    """
    Display gallery of highlight videos.

    Shows:
    - Highlights organized by player (alphabetically)
    - Unassociated highlights (not linked to any score)
    - Total highlight count
    - Edit buttons for staff users
    """

    template_name = 'superb_ock/highlights/highlights.html'

    def get(self, request):
        """Display highlights gallery."""
        # Get all scores with highlights and related data - ordered by player first name
        scores_with_highlights = Score.objects.select_related(
            'player', 'hole__golf_course', 'golf_round'
        ).prefetch_related('highlight__previews').filter(
            highlight__isnull=False
        ).order_by('player__first_name', 'player__second_name').distinct()

        # Get all highlights to find unassociated ones
        all_highlights = Highlight.objects.prefetch_related('previews').all()
        associated_highlight_ids = set()

        # Organize highlights by player (with player object for sorting)
        player_highlights = {}

        for score in scores_with_highlights:
            if score.player and score.player.first_name and score.player.second_name:
                # Use player object as key to maintain sorting info
                player_key = (score.player.first_name, score.player.second_name, score.player)

                if player_key not in player_highlights:
                    player_highlights[player_key] = []

                # Add each highlight for this score
                for highlight in score.highlight.all():
                    associated_highlight_ids.add(highlight.pk)
                    highlight_with_context = {
                        'highlight': highlight,
                        'score': score,
                        'hole': score.hole,
                        'course': score.hole.golf_course if score.hole else None,
                        'round': score.golf_round
                    }
                    player_highlights[player_key].append(highlight_with_context)

        # Find unassociated highlights
        unassociated_highlights = []
        for highlight in all_highlights:
            if highlight.pk not in associated_highlight_ids:
                unassociated_highlights.append({'highlight': highlight})

        # Sort players by first name, then second name (same as scorecard)
        sorted_players = []
        for (first_name, second_name, player_obj), highlights in sorted(player_highlights.items()):
            player_name = f"{first_name} {second_name}"
            sorted_players.append((player_name, highlights))

        context = {
            'player_highlights': sorted_players,
            'unassociated_highlights': unassociated_highlights,
            'total_highlights': all_highlights.count()
        }

        return render(request, self.template_name, context)
