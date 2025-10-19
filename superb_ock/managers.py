"""
Custom QuerySet managers for optimized database queries.

Centralizes common query patterns and optimizations to reduce code duplication
and prevent N+1 query problems.
"""

from django.db import models


class ScoreQuerySet(models.QuerySet):
    """
    Custom QuerySet for Score model with common query optimizations.

    Provides reusable methods that automatically include select_related and
    prefetch_related for frequently accessed related objects.
    """

    def with_related_data(self):
        """
        Include all commonly accessed related objects.

        Optimizes queries by fetching:
        - player (first_name, second_name)
        - hole (hole_number, par, golf_course)
        - golf_course (name, tees, country)
        - golf_round (date_started, event)
        - event (name, scoring)

        Returns:
            QuerySet with optimized joins
        """
        return self.select_related(
            'player',
            'hole',
            'hole__golf_course',
            'golf_round',
            'golf_round__event'
        )

    def for_round(self, round_id):
        """
        Get all scores for a specific round with related data.

        Args:
            round_id: GolfRound ID

        Returns:
            QuerySet filtered by round with optimized joins
        """
        return self.filter(golf_round_id=round_id).with_related_data()

    def for_player(self, player):
        """
        Get all scores for a specific player with related data.

        Args:
            player: Player instance or player_id

        Returns:
            QuerySet filtered by player with optimized joins
        """
        return self.filter(player=player).with_related_data()

    def for_course(self, course):
        """
        Get all scores for a specific golf course with related data.

        Args:
            course: GolfCourse instance or course_id

        Returns:
            QuerySet filtered by course with optimized joins
        """
        return self.filter(hole__golf_course=course).with_related_data()

    def for_event(self, event_id):
        """
        Get all scores for a specific event with related data.

        Args:
            event_id: GolfEvent ID

        Returns:
            QuerySet filtered by event with optimized joins
        """
        return self.filter(golf_round__event_id=event_id).with_related_data()

    def with_highlights(self):
        """
        Prefetch highlights for all scores to avoid N+1 queries.

        Use this when displaying scores with their associated video highlights.

        Returns:
            QuerySet with prefetched highlights
        """
        return self.prefetch_related('highlight')

    def with_all_related(self):
        """
        Include all related data including highlights.

        Most complete optimization - use when displaying full score details.

        Returns:
            QuerySet with all optimizations
        """
        return self.with_related_data().with_highlights()


class GolfRoundQuerySet(models.QuerySet):
    """
    Custom QuerySet for GolfRound model with common query optimizations.
    """

    def with_event(self):
        """
        Include event data to avoid additional queries.

        Returns:
            QuerySet with event data
        """
        return self.select_related('event')

    def for_event(self, event_id):
        """
        Get all rounds for a specific event.

        Args:
            event_id: GolfEvent ID

        Returns:
            QuerySet filtered by event with event data
        """
        return self.filter(event_id=event_id).with_event()

    def recent(self, limit=10):
        """
        Get most recent rounds ordered by date.

        Args:
            limit: Maximum number of rounds to return

        Returns:
            QuerySet of recent rounds
        """
        return self.with_event().order_by('-date_started', '-id')[:limit]


class HighlightQuerySet(models.QuerySet):
    """
    Custom QuerySet for Highlight model with common query optimizations.
    """

    def with_previews(self):
        """
        Prefetch preview images to avoid N+1 queries.

        Returns:
            QuerySet with prefetched previews
        """
        return self.prefetch_related('previews')

    def with_scores(self):
        """
        Prefetch related scores to avoid N+1 queries.

        Returns:
            QuerySet with prefetched scores
        """
        return self.prefetch_related('score_set')

    def with_all_related(self):
        """
        Include all related data.

        Returns:
            QuerySet with all optimizations
        """
        return self.with_previews().with_scores()


# Manager classes that use the custom QuerySets
class ScoreManager(models.Manager):
    """Manager for Score model using ScoreQuerySet."""
    def get_queryset(self):
        return ScoreQuerySet(self.model, using=self._db)

    # Expose QuerySet methods on the manager
    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def for_round(self, round_id):
        return self.get_queryset().for_round(round_id)

    def for_player(self, player):
        return self.get_queryset().for_player(player)

    def for_course(self, course):
        return self.get_queryset().for_course(course)

    def for_event(self, event_id):
        return self.get_queryset().for_event(event_id)

    def with_highlights(self):
        return self.get_queryset().with_highlights()

    def with_all_related(self):
        return self.get_queryset().with_all_related()


class GolfRoundManager(models.Manager):
    """Manager for GolfRound model using GolfRoundQuerySet."""
    def get_queryset(self):
        return GolfRoundQuerySet(self.model, using=self._db)

    def with_event(self):
        return self.get_queryset().with_event()

    def for_event(self, event_id):
        return self.get_queryset().for_event(event_id)

    def recent(self, limit=10):
        return self.get_queryset().recent(limit)


class HighlightManager(models.Manager):
    """Manager for Highlight model using HighlightQuerySet."""
    def get_queryset(self):
        return HighlightQuerySet(self.model, using=self._db)

    def with_previews(self):
        return self.get_queryset().with_previews()

    def with_scores(self):
        return self.get_queryset().with_scores()

    def with_all_related(self):
        return self.get_queryset().with_all_related()
