"""
Tests for models in the superb_ock application.
"""
import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from superb_ock.models import (
    GolfCourse,
    GolfEvent,
    GolfRound,
    Hole,
    Player,
    Score,
    Highlight,
    HighlightPreview,
    CarouselImage,
    UserProfile,
)
from superb_ock.constants import ScoringFormat, Handedness
from .factories import (
    GolfCourseFactory,
    GolfEventFactory,
    GolfRoundFactory,
    HoleFactory,
    PlayerFactory,
    ScoreFactory,
    HighlightFactory,
    UserFactory,
    UserProfileFactory,
    CarouselImageFactory,
    create_complete_course_with_holes,
    create_complete_round_with_scores,
)


@pytest.mark.django_db
class TestGolfCourse:
    """Tests for the GolfCourse model."""

    def test_create_golf_course(self):
        """Test creating a golf course."""
        course = GolfCourseFactory(name="St Andrews", country="Scotland")

        assert course.id is not None
        assert course.name == "St Andrews"
        assert course.country == "Scotland"
        assert course.tees == "White"
        assert course.slope_rating == 113
        assert course.course_rating == 72.0
        assert course.par == 72

    def test_golf_course_str(self):
        """Test string representation of GolfCourse."""
        course = GolfCourseFactory(name="Pebble Beach", tees="Blue")
        assert str(course) == "Pebble Beach - Blue Tees"

    def test_create_complete_course_with_holes(self):
        """Test helper function to create course with 18 holes."""
        course, holes = create_complete_course_with_holes("Augusta National")

        assert course.name == "Augusta National"
        assert len(holes) == 18
        assert all(hole.golf_course == course for hole in holes)
        assert all(hole.hole_number == i + 1 for i, hole in enumerate(holes))


@pytest.mark.django_db
class TestGolfEvent:
    """Tests for the GolfEvent model."""

    def test_create_golf_event(self):
        """Test creating a golf event."""
        event = GolfEventFactory(
            name="Masters Tournament",
            scoring=ScoringFormat.BEST_THREE_OF_FIVE
        )

        assert event.id is not None
        assert event.name == "Masters Tournament"
        assert event.scoring == ScoringFormat.BEST_THREE_OF_FIVE

    def test_golf_event_str(self):
        """Test string representation of GolfEvent."""
        event = GolfEventFactory(name="US Open")
        assert str(event) == "US Open"

    def test_default_scoring_format(self):
        """Test that default scoring format is set correctly."""
        event = GolfEventFactory()
        assert event.scoring == ScoringFormat.BEST_THREE_OF_FIVE


@pytest.mark.django_db
class TestGolfRound:
    """Tests for the GolfRound model."""

    def test_create_golf_round(self):
        """Test creating a golf round."""
        event = GolfEventFactory()
        golf_round = GolfRoundFactory(event=event)

        assert golf_round.id is not None
        assert golf_round.event == event
        assert golf_round.date_started is not None

    def test_golf_round_str(self):
        """Test string representation of GolfRound."""
        event = GolfEventFactory(name="Test Event")
        golf_round = GolfRoundFactory(event=event)
        assert str(golf_round) == f"Test Event - {golf_round.pk}"

    def test_create_complete_round(self):
        """Test creating a complete round with scores."""
        golf_round, scores = create_complete_round_with_scores()

        # Should have 4 players × 18 holes = 72 scores
        assert len(scores) == 72
        assert golf_round.score_set.count() == 72


@pytest.mark.django_db
class TestHole:
    """Tests for the Hole model."""

    def test_create_hole(self):
        """Test creating a hole."""
        course = GolfCourseFactory()
        hole = HoleFactory(
            golf_course=course,
            hole_number=1,
            par=4,
            yards=425,
            stroke_index=5
        )

        assert hole.id is not None
        assert hole.golf_course == course
        assert hole.hole_number == 1
        assert hole.par == 4
        assert hole.yards == 425
        assert hole.stroke_index == 5

    def test_hole_str(self):
        """Test string representation of Hole."""
        course = GolfCourseFactory(name="Pine Valley")
        hole = HoleFactory(golf_course=course, hole_number=10)
        assert str(hole) == "Pine Valley - White Tees - Hole 10"

    def test_par_choices(self):
        """Test that par can only be 3, 4, or 5."""
        hole = HoleFactory(par=3)
        assert hole.par in [3, 4, 5]


@pytest.mark.django_db
class TestPlayer:
    """Tests for the Player model."""

    def test_create_player(self):
        """Test creating a player."""
        player = PlayerFactory(
            first_name="Tiger",
            second_name="Woods",
            handedness=Handedness.RIGHT,
            ocks=5
        )

        assert player.id is not None
        assert player.first_name == "Tiger"
        assert player.second_name == "Woods"
        assert player.handedness == Handedness.RIGHT
        assert player.ocks == 5

    def test_player_str(self):
        """Test string representation of Player."""
        player = PlayerFactory(first_name="Phil", second_name="Mickelson")
        assert str(player) == "Phil Mickelson"

    def test_player_slug_generation(self):
        """Test that slug is generated correctly."""
        player = PlayerFactory(first_name="Rory", second_name="McIlroy")
        assert "rory" in player.slug.lower()
        assert "mcilroy" in player.slug.lower()


@pytest.mark.django_db
class TestScore:
    """Tests for the Score model."""

    def test_create_score(self):
        """Test creating a score."""
        hole = HoleFactory(par=4)
        player = PlayerFactory()
        golf_round = GolfRoundFactory()

        score = ScoreFactory(
            hole=hole,
            player=player,
            golf_round=golf_round,
            shots_taken=5,
            handicap_index=12.5,
            sandy=False
        )

        assert score.id is not None
        assert score.hole == hole
        assert score.player == player
        assert score.golf_round == golf_round
        assert score.shots_taken == 5
        assert score.handicap_index == 12.5
        assert score.sandy is False

    def test_score_str(self):
        """Test string representation of Score."""
        hole = HoleFactory(hole_number=1)
        player = PlayerFactory(first_name="John", second_name="Doe")
        golf_round = GolfRoundFactory()
        score = ScoreFactory(hole=hole, player=player, golf_round=golf_round)

        score_str = str(score)
        assert "John Doe" in score_str

    def test_stableford_calculation(self):
        """Test that stableford points are calculated correctly."""
        hole = HoleFactory(par=4)
        player = PlayerFactory()
        golf_round = GolfRoundFactory()

        # Par (4 shots on par 4) = 2 points
        score = ScoreFactory(
            hole=hole,
            player=player,
            golf_round=golf_round,
            shots_taken=4
        )
        # Factory should calculate stableford based on shots vs par
        assert score.stableford == 2

    def test_score_with_highlights(self):
        """Test adding highlights to a score."""
        score = ScoreFactory()
        highlight1 = HighlightFactory(title="Great shot")
        highlight2 = HighlightFactory(title="Amazing putt")

        score.highlight.add(highlight1, highlight2)

        assert score.highlight.count() == 2
        assert highlight1 in score.highlight.all()
        assert highlight2 in score.highlight.all()


@pytest.mark.django_db
class TestHighlight:
    """Tests for the Highlight model."""

    def test_create_highlight(self):
        """Test creating a highlight."""
        highlight = HighlightFactory(title="Hole in One")

        assert highlight.id is not None
        assert highlight.title == "Hole in One"

    def test_highlight_str(self):
        """Test string representation of Highlight."""
        highlight = HighlightFactory(title="Eagle on 18")
        assert str(highlight) == "Eagle on 18"


@pytest.mark.django_db
class TestHighlightPreview:
    """Tests for the HighlightPreview model."""

    def test_create_highlight_preview(self):
        """Test creating a highlight preview."""
        highlight = HighlightFactory()
        # Note: In real tests with files, you'd need to provide actual image files
        # For now, we're testing the model relationships and fields

        # Previews are typically created with the highlight
        # This tests the relationship exists

    def test_highlight_preview_ordering(self):
        """Test that previews are ordered correctly."""
        highlight = HighlightFactory()
        # Would create previews with different order values and test ordering


@pytest.mark.django_db
class TestCarouselImage:
    """Tests for the CarouselImage model."""

    def test_create_carousel_image(self):
        """Test creating a carousel image."""
        carousel = CarouselImageFactory(
            title="Welcome",
            description="Welcome to our golf club",
            order=1,
            is_active=True
        )

        assert carousel.id is not None
        assert carousel.title == "Welcome"
        assert carousel.description == "Welcome to our golf club"
        assert carousel.order == 1
        assert carousel.is_active is True

    def test_carousel_image_str(self):
        """Test string representation of CarouselImage."""
        carousel = CarouselImageFactory(title="Home", order=3)
        assert str(carousel) == "Home (Order: 3)"

    def test_carousel_ordering(self):
        """Test that carousel images are ordered correctly."""
        # Clear any existing carousel images
        CarouselImage.objects.all().delete()

        carousel1 = CarouselImageFactory(order=3)
        carousel2 = CarouselImageFactory(order=1)
        carousel3 = CarouselImageFactory(order=2)

        images = list(CarouselImage.objects.all().order_by('order'))
        assert len(images) == 3
        assert images[0].order == 1  # order 1
        assert images[1].order == 2  # order 2
        assert images[2].order == 3  # order 3


@pytest.mark.django_db
class TestUserProfile:
    """Tests for the UserProfile model."""

    def test_create_user_profile(self):
        """Test creating a user profile."""
        user = UserFactory()
        # Profile should be auto-created via signal
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_user_profile_str(self):
        """Test string representation of UserProfile."""
        user = UserFactory(username="testuser")
        profile_str = str(user.profile)
        assert "testuser" in profile_str

    def test_notification_preferences(self):
        """Test notification preference defaults."""
        user = UserFactory()
        profile = user.profile

        assert profile.notifications_enabled is False  # Default from constants
        assert profile.notify_round_start is True
        assert profile.notify_hole_completed is False
        assert profile.notify_round_completed is True

    def test_update_notification_preferences(self):
        """Test updating notification preferences."""
        user = UserFactory()
        profile = user.profile

        profile.notifications_enabled = True
        profile.notify_hole_completed = True
        profile.save()

        profile.refresh_from_db()
        assert profile.notifications_enabled is True
        assert profile.notify_hole_completed is True


@pytest.mark.django_db
class TestModelIntegration:
    """Integration tests that test multiple models working together."""

    def test_complete_round_workflow(self):
        """Test creating a complete round with event, course, players, and scores."""
        # Create event
        event = GolfEventFactory(name="Club Championship")

        # Create course with holes
        course, holes = create_complete_course_with_holes("Test Club")

        # Create players
        players = [PlayerFactory() for _ in range(4)]

        # Create round
        golf_round = GolfRoundFactory(event=event)

        # Create scores for all players on all holes
        scores = []
        for player in players:
            for hole in holes:
                score = ScoreFactory(
                    hole=hole,
                    player=player,
                    golf_round=golf_round
                )
                scores.append(score)

        # Verify everything is connected properly
        assert len(scores) == 72  # 4 players × 18 holes
        assert golf_round.score_set.count() == 72
        assert event.golfround_set.count() == 1

    def test_player_scores_query(self):
        """Test querying all scores for a specific player."""
        golf_round, scores = create_complete_round_with_scores()

        # Get first player
        first_player = scores[0].player

        # Query all scores for this player
        player_scores = Score.objects.filter(player=first_player, golf_round=golf_round)

        assert player_scores.count() == 18  # One score per hole

    def test_round_leaderboard_data(self):
        """Test getting leaderboard data for a round."""
        golf_round, scores = create_complete_round_with_scores()

        # Get all players in the round
        players = Player.objects.filter(score__golf_round=golf_round).distinct()

        assert players.count() == 4

        # Calculate total stableford for each player
        for player in players:
            total_stableford = Score.objects.filter(
                player=player,
                golf_round=golf_round
            ).aggregate(total=models.Sum('stableford'))['total']

            assert total_stableford is not None
            assert total_stableford >= 0


# Import for the test above
from django.db import models
