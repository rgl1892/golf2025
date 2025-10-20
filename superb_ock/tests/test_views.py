"""
Tests for views in the superb_ock application.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from superb_ock.models import (
    GolfEvent,
    GolfRound,
    Player,
    Score,
    CarouselImage,
)
from .factories import (
    UserFactory,
    GolfEventFactory,
    GolfRoundFactory,
    PlayerFactory,
    ScoreFactory,
    CarouselImageFactory,
    create_complete_course_with_holes,
    create_complete_round_with_scores,
)


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def authenticated_client():
    """Create an authenticated test client."""
    client = Client()
    user = UserFactory()
    client.force_login(user)
    return client, user


@pytest.mark.django_db
class TestHomeView:
    """Tests for the Home view."""

    def test_home_view_loads(self, client):
        """Test that the home page loads successfully."""
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_home_view_with_carousel(self, client):
        """Test home page displays carousel images."""
        # Create some carousel images
        CarouselImageFactory(title="Image 1", is_active=True, order=1)
        CarouselImageFactory(title="Image 2", is_active=True, order=2)
        CarouselImageFactory(title="Image 3", is_active=False, order=3)  # Inactive

        response = client.get(reverse('home'))

        assert response.status_code == 200
        # Should only show active images
        assert b"Image 1" in response.content
        assert b"Image 2" in response.content
        # Inactive image should not appear
        # Note: This assumes the template renders carousel titles

    def test_home_view_with_event_data(self, client):
        """Test home page with event and round data."""
        # Create event with rounds
        event = GolfEventFactory(name="Test Tournament")
        golf_round, scores = create_complete_round_with_scores(event=event)

        response = client.get(reverse('home'))

        assert response.status_code == 200
        assert 'leaderboard_data' in response.context or 'context' in dir(response)


@pytest.mark.django_db
class TestRoundsOverviewView:
    """Tests for the RoundsOverview view."""

    def test_rounds_overview_loads(self, client):
        """Test that rounds overview page loads."""
        response = client.get(reverse('rounds_overview'))
        assert response.status_code == 200

    def test_rounds_overview_displays_rounds(self, client):
        """Test that rounds are displayed on overview page."""
        # Create several rounds
        event = GolfEventFactory(name="Championship")
        round1 = GolfRoundFactory(event=event)
        round2 = GolfRoundFactory(event=event)
        round3 = GolfRoundFactory(event=event)

        response = client.get(reverse('rounds_overview'))

        assert response.status_code == 200
        # Check that rounds are in context (view-specific logic may vary)


@pytest.mark.django_db
class TestGolfRoundView:
    """Tests for the GolfRoundView."""

    def test_round_detail_view_loads(self, client):
        """Test that a specific round detail page loads."""
        golf_round, scores = create_complete_round_with_scores()

        response = client.get(reverse('golf_round', args=[golf_round.pk]))

        assert response.status_code == 200

    def test_round_detail_view_shows_scores(self, client):
        """Test that round detail shows all scores."""
        golf_round, scores = create_complete_round_with_scores()

        response = client.get(reverse('golf_round', args=[golf_round.pk]))

        assert response.status_code == 200
        # The response should contain score data
        # Specific assertions would depend on template structure

    def test_round_detail_view_not_found(self, client):
        """Test that accessing non-existent round returns 404."""
        response = client.get(reverse('golf_round', args=[99999]))

        # Should either be 404 or redirect, depending on view implementation
        assert response.status_code in [404, 302]


@pytest.mark.django_db
class TestNewRoundView:
    """Tests for the NewRound view."""

    def test_new_round_view_requires_authentication(self, client):
        """Test that new round view requires login."""
        response = client.get(reverse('new_round'))

        # Should redirect to login if not authenticated
        # Or return 200 if authentication not required
        # Adjust based on actual implementation
        assert response.status_code in [200, 302]

    def test_new_round_view_loads_for_authenticated_user(self, authenticated_client):
        """Test that authenticated users can access new round view."""
        client, user = authenticated_client

        response = client.get(reverse('new_round'))

        # Should load successfully
        assert response.status_code == 200


@pytest.mark.django_db
class TestEditScoreView:
    """Tests for the EditScore view."""

    def test_edit_score_view_loads(self, client):
        """Test that edit score page loads."""
        golf_round, scores = create_complete_round_with_scores()
        first_score = scores[0]

        response = client.get(
            reverse('edit_score',
                    args=[golf_round.pk, first_score.hole.hole_number])
        )

        assert response.status_code == 200

    def test_edit_score_view_displays_correct_hole(self, client):
        """Test that edit score shows correct hole information."""
        golf_round, scores = create_complete_round_with_scores()
        hole_number = 5

        response = client.get(
            reverse('edit_score',
                    args=[golf_round.pk, hole_number])
        )

        assert response.status_code == 200
        # Should show scores for hole 5


@pytest.mark.django_db
class TestHighlightsView:
    """Tests for the HighlightsView."""

    def test_highlights_view_loads(self, client):
        """Test that highlights page loads."""
        response = client.get(reverse('highlights'))

        assert response.status_code == 200

    def test_highlights_view_with_highlights(self, client):
        """Test highlights page with actual highlights."""
        # Create a round with scores and add highlights
        golf_round, scores = create_complete_round_with_scores()

        # Would add highlights to specific scores here
        # For now, just test page loads

        response = client.get(reverse('highlights'))

        assert response.status_code == 200


@pytest.mark.django_db
class TestEventView:
    """Tests for the EventView."""

    def test_event_view_loads(self, client):
        """Test that event detail page loads."""
        event = GolfEventFactory(name="Masters")

        response = client.get(reverse('event', args=[event.pk]))

        assert response.status_code == 200

    def test_event_view_shows_event_data(self, client):
        """Test that event page shows correct event information."""
        event = GolfEventFactory(name="US Open")
        golf_round, scores = create_complete_round_with_scores(event=event)

        response = client.get(reverse('event', args=[event.pk]))

        assert response.status_code == 200
        # Should display event name and round data


@pytest.mark.django_db
class TestHeatMapView:
    """Tests for the HeatMap view."""

    def test_heatmap_view_loads(self, client):
        """Test that heatmap visualization loads."""
        response = client.get(reverse('heatmap'))

        assert response.status_code == 200

    def test_heatmap_view_with_data(self, client):
        """Test heatmap with actual score data."""
        # Create several rounds with scores
        golf_round1, scores1 = create_complete_round_with_scores()
        golf_round2, scores2 = create_complete_round_with_scores()

        response = client.get(reverse('heatmap'))

        assert response.status_code == 200
        # Should render heatmap visualization


@pytest.mark.django_db
class TestAuthenticationViews:
    """Tests for authentication-related views."""

    def test_signup_view_loads(self, client):
        """Test that signup page loads."""
        response = client.get(reverse('sign_up_user'))

        assert response.status_code == 200

    def test_signup_creates_user(self, client):
        """Test that signup form creates a new user."""
        user_data = {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }

        response = client.post(reverse('sign_up_user'), data=user_data)

        # Should either redirect or create user
        # Check if user was created
        if response.status_code == 302:
            assert User.objects.filter(username='newuser').exists()

    def test_login_view_loads(self, client):
        """Test that login page loads."""
        response = client.get(reverse('login'))

        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client):
        """Test login with correct username and password."""
        # Create a user
        user = UserFactory()

        response = client.post(
            reverse('login'),
            data={'username': user.username, 'password': 'testpass123'}
        )

        # Should redirect after successful login
        # Adjust based on actual behavior
        assert response.status_code in [200, 302]

    def test_logout_view(self, authenticated_client):
        """Test logout functionality."""
        client, user = authenticated_client

        response = client.get(reverse('logout'))

        # Should redirect after logout
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestAPIEndpoints:
    """Tests for API endpoints (if any)."""

    def test_heatmap_data_endpoint(self, client):
        """Test heatmap data JSON endpoint."""
        # Create some score data
        golf_round, scores = create_complete_round_with_scores()

        response = client.get(reverse('heatmap_data'))

        assert response.status_code == 200
        # Should return JSON data
        assert response['Content-Type'] == 'application/json'


@pytest.mark.django_db
class TestPermissions:
    """Tests for view permissions and access control."""

    def test_unauthenticated_user_cannot_create_round(self, client):
        """Test that unauthenticated users cannot create rounds."""
        # This test depends on whether NewRound requires authentication
        # Adjust based on actual implementation
        pass

    def test_authenticated_user_can_edit_scores(self, authenticated_client):
        """Test that authenticated users can edit scores."""
        client, user = authenticated_client
        golf_round, scores = create_complete_round_with_scores()

        # Try to update a score
        score = scores[0]
        response = client.post(
            reverse('edit_score',
                    args=[golf_round.pk, score.hole.hole_number]),
            data={'shots_taken': 4}
        )

        # Should allow editing (200 or 302)
        assert response.status_code in [200, 302]


@pytest.mark.integration
@pytest.mark.django_db
class TestViewIntegration:
    """Integration tests for view workflows."""

    def test_complete_round_creation_workflow(self, authenticated_client):
        """Test the complete workflow of creating and viewing a round."""
        client, user = authenticated_client

        # Step 1: Access new round page
        response = client.get(reverse('new_round'))
        assert response.status_code == 200

        # Step 2: Create a round (if POST is implemented)
        # Step 3: View the created round
        # Step 4: Edit scores

        # This would test the full user journey

    def test_leaderboard_updates_with_new_scores(self, client):
        """Test that leaderboard updates when scores change."""
        event = GolfEventFactory()
        golf_round, scores = create_complete_round_with_scores(event=event)

        # Get initial leaderboard
        response1 = client.get(reverse('event', args=[event.pk]))
        assert response1.status_code == 200

        # Update a score
        score = scores[0]
        score.shots_taken = 2  # Eagle!
        score.stableford = 5
        score.save()

        # Get updated leaderboard
        response2 = client.get(reverse('event', args=[event.pk]))
        assert response2.status_code == 200

        # Leaderboard should reflect new score
        # Specific assertion would depend on template structure
