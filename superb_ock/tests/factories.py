"""
Factory Boy factories for creating test data.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth.models import User

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

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating Django User instances."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user is created."""
        if create:
            obj.set_password(extracted or 'testpass123')


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    notifications_enabled = True
    notify_round_start = True
    notify_hole_completed = False
    notify_round_completed = True


class GolfCourseFactory(DjangoModelFactory):
    """Factory for creating GolfCourse instances."""

    class Meta:
        model = GolfCourse

    name = factory.Sequence(lambda n: f"Golf Club {n}")
    country = "Scotland"
    tees = "White"
    slope_rating = 113
    course_rating = 72.0
    par = 72
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))


class GolfEventFactory(DjangoModelFactory):
    """Factory for creating GolfEvent instances."""

    class Meta:
        model = GolfEvent

    name = factory.Sequence(lambda n: f"Tournament {n}")
    scoring = ScoringFormat.BEST_THREE_OF_FIVE


class GolfRoundFactory(DjangoModelFactory):
    """Factory for creating GolfRound instances."""

    class Meta:
        model = GolfRound

    event = factory.SubFactory(GolfEventFactory)
    date_started = factory.Faker('date_this_year')


class HoleFactory(DjangoModelFactory):
    """Factory for creating Hole instances."""

    class Meta:
        model = Hole

    hole_number = factory.Sequence(lambda n: (n % 18) + 1)
    golf_course = factory.SubFactory(GolfCourseFactory)
    par = 4
    yards = 400
    stroke_index = factory.Sequence(lambda n: (n % 18) + 1)


class PlayerFactory(DjangoModelFactory):
    """Factory for creating Player instances."""

    class Meta:
        model = Player

    first_name = factory.Faker('first_name')
    second_name = factory.Faker('last_name')
    ocks = 0
    handedness = Handedness.RIGHT
    info = factory.Faker('text', max_nb_chars=200)
    slug = factory.LazyAttribute(
        lambda obj: f"{obj.first_name}-{obj.second_name}".lower().replace(' ', '-')
    )


class HighlightFactory(DjangoModelFactory):
    """Factory for creating Highlight instances."""

    class Meta:
        model = Highlight

    title = factory.Sequence(lambda n: f"Highlight {n}")
    # Note: video and thumbnail fields will need to be handled separately in tests
    # that require actual file uploads


class HighlightPreviewFactory(DjangoModelFactory):
    """Factory for creating HighlightPreview instances."""

    class Meta:
        model = HighlightPreview

    highlight = factory.SubFactory(HighlightFactory)
    timestamp = factory.Faker('pyfloat', positive=True, max_value=300.0)
    order = factory.Sequence(lambda n: n % 3)


class ScoreFactory(DjangoModelFactory):
    """Factory for creating Score instances."""

    class Meta:
        model = Score

    shots_taken = factory.Faker('random_int', min=2, max=8)
    stableford = factory.LazyAttribute(lambda obj: max(0, 2 - (obj.shots_taken - obj.hole.par)))
    hole = factory.SubFactory(HoleFactory)
    player = factory.SubFactory(PlayerFactory)
    golf_round = factory.SubFactory(GolfRoundFactory)
    handicap_index = factory.Faker('pyfloat', positive=True, max_value=36.0)
    sandy = False


class CarouselImageFactory(DjangoModelFactory):
    """Factory for creating CarouselImage instances."""

    class Meta:
        model = CarouselImage

    title = factory.Sequence(lambda n: f"Carousel {n}")
    description = factory.Faker('text', max_nb_chars=200)
    order = factory.Sequence(lambda n: n)
    is_active = True
    focal_point_x = 50
    focal_point_y = 50


def create_complete_course_with_holes(course_name="Test Course"):
    """
    Helper function to create a complete golf course with all 18 holes.

    Args:
        course_name: Name for the golf course

    Returns:
        Tuple of (GolfCourse, List[Hole])
    """
    course = GolfCourseFactory(name=course_name)
    holes = []

    # Create 18 holes with realistic pars
    par_sequence = [4, 4, 3, 5, 4, 4, 3, 4, 5,  # Front 9
                    4, 3, 5, 4, 4, 3, 4, 5, 4]  # Back 9

    for i in range(18):
        hole = HoleFactory(
            golf_course=course,
            hole_number=i + 1,
            par=par_sequence[i],
            stroke_index=i + 1
        )
        holes.append(hole)

    return course, holes


def create_complete_round_with_scores(event=None, players=None, course=None):
    """
    Helper function to create a complete round with all scores for all players.

    Args:
        event: GolfEvent instance (creates one if None)
        players: List of Player instances (creates 4 if None)
        course: GolfCourse instance (creates one with holes if None)

    Returns:
        Tuple of (GolfRound, List[Score])
    """
    if event is None:
        event = GolfEventFactory()

    if players is None:
        players = [PlayerFactory() for _ in range(4)]

    if course is None:
        course, holes = create_complete_course_with_holes()
    else:
        holes = list(course.hole_set.all().order_by('hole_number'))
        if len(holes) != 18:
            raise ValueError("Course must have exactly 18 holes")

    golf_round = GolfRoundFactory(event=event)
    scores = []

    # Create scores for each player on each hole
    for player in players:
        for hole in holes:
            score = ScoreFactory(
                hole=hole,
                player=player,
                golf_round=golf_round
            )
            scores.append(score)

    return golf_round, scores
