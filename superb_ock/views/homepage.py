"""
Homepage view displaying tournament leaderboard and recent rounds.
"""
from django.shortcuts import render
from django.views import View

from ..models import CarouselImage, GolfRound


class Home(View):
    """
    Main homepage view.

    Displays:
    - Tournament leaderboard (Event ID 5)
    - Carousel images
    - Recent rounds
    """

    template_name = "superb_ock/homepage/home.html"

    def get_context(self):
        """
        Build context data for homepage.

        Returns:
            Dict containing leaderboard, courses, carousel images, and recent rounds
        """
        # Use DateCourseLeaderboardBuilder service to generate leaderboard
        # Event ID 5 is hardcoded for the main tournament homepage
        from ..services.leaderboard import DateCourseLeaderboardBuilder

        builder = DateCourseLeaderboardBuilder(event_id=5)
        entries = builder.build()

        # Convert to template-compatible format
        cleaned_leaderboard = builder.to_dict_format(entries)
        courses = builder.get_courses_list(entries)

        # Get active carousel images
        carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order', '-created_at')

        # Get last 5 rounds played
        recent_rounds = (
            GolfRound.objects
            .select_related('event')
            .prefetch_related('score_set__hole__golf_course', 'score_set__player')
            .order_by('-date_started', '-id')[:5]
        )

        # Process recent rounds data
        recent_rounds_data = []
        for round_obj in recent_rounds:
            scores = round_obj.score_set.all()
            if scores:
                # Get course info from first score
                first_score = scores[0]
                course_name = f"{first_score.hole.golf_course.name} - {first_score.hole.golf_course.tees}"

                # Get players and their totals
                player_totals = {}
                for score in scores:
                    player_name = f"{score.player.first_name} {score.player.second_name}"
                    if player_name not in player_totals:
                        player_totals[player_name] = {'stableford': 0, 'shots': 0}
                    player_totals[player_name]['stableford'] += score.stableford or 0
                    player_totals[player_name]['shots'] += score.shots_taken or 0

                # Sort players by stableford points
                sorted_players = sorted(
                    player_totals.items(),
                    key=lambda x: x[1]['stableford'],
                    reverse=True
                )

                recent_rounds_data.append({
                    'id': round_obj.id,
                    'date': round_obj.date_started,
                    'event': round_obj.event.name,
                    'course': course_name,
                    'players': sorted_players[:4],  # Show top 4 players
                    'total_players': len(player_totals)
                })

        context = {
            'leaderboard': cleaned_leaderboard,
            'courses': courses,
            'carousel_images': carousel_images,
            'recent_rounds': recent_rounds_data
        }
        return context

    def get(self, request):
        """Handle GET request for homepage."""
        context = self.get_context()

        # Check if we should show the welcome modal for new users
        if request.session.pop('show_welcome_modal', False):
            context['show_welcome_modal'] = True

        return render(request, self.template_name, context=context)
