# Golf2025 Refactoring Plan

## Overview
This document outlines a comprehensive refactoring plan to improve maintainability, readability, and flexibility of the golf2025 codebase.

---

## Phase 1: Extract Business Logic (HIGH PRIORITY)

### 1.1 Create Constants Module
**File:** `superb_ock/constants.py`

```python
# Golf game constants
HOLES_PER_ROUND = 18
MAX_PLAYERS_PER_ROUND = 4

# Scoring formats
class ScoringFormat:
    BEST_THREE_OF_FIVE = 'best_three_of_five'
    BEST_LAST_ROUNDS_COUNTS = 'best_last_rounds_counts'

    CHOICES = [
        (BEST_THREE_OF_FIVE, 'Best 3 of 5'),
        (BEST_LAST_ROUNDS_COUNTS, 'Best Last Rounds Count'),
    ]

# Par values
PAR_VALUES = [3, 4, 5]

# Thumbnail generation settings
THUMBNAIL_QUALITY = 95
PREVIEW_COUNT = 3
PREVIEW_POSITIONS = [0.25, 0.5, 0.75]  # 25%, 50%, 75% through video
```

**Impact:** Eliminates magic numbers throughout codebase
**Effort:** 1 hour
**Files affected:** 15+ files currently using hardcoded values

---

### 1.2 Create Scoring Calculator Service
**File:** `superb_ock/services/scoring.py`

```python
from typing import List, Dict, Optional
from django.db.models import QuerySet
from superb_ock.models import Score, GolfRound
from superb_ock.constants import ScoringFormat


class ScoringCalculator:
    """
    Centralized scoring calculation logic.
    Handles different scoring formats and counting rounds.
    """

    def __init__(self, scoring_format: str):
        self.scoring_format = scoring_format

    def calculate_total(
        self,
        scores: QuerySet[Score],
        player_id: int
    ) -> int:
        """Calculate total stableford points for a player."""
        if self.scoring_format == ScoringFormat.BEST_THREE_OF_FIVE:
            return self._calculate_best_three_of_five(scores, player_id)
        elif self.scoring_format == ScoringFormat.BEST_LAST_ROUNDS_COUNTS:
            return self._calculate_best_last_rounds(scores, player_id)
        return 0

    def get_counting_rounds(
        self,
        rounds: QuerySet[GolfRound],
        player_id: int
    ) -> List[int]:
        """Return list of round IDs that count towards total."""
        # Implementation here
        pass

    def is_counting_round(
        self,
        round_id: int,
        player_id: int,
        all_rounds: QuerySet[GolfRound]
    ) -> bool:
        """Check if a specific round counts towards player total."""
        counting_rounds = self.get_counting_rounds(all_rounds, player_id)
        return round_id in counting_rounds

    def _calculate_best_three_of_five(
        self,
        scores: QuerySet[Score],
        player_id: int
    ) -> int:
        """Best 3 of 5 rounds scoring."""
        # Extract existing logic from Home view
        pass

    def _calculate_best_last_rounds(
        self,
        scores: QuerySet[Score],
        player_id: int
    ) -> int:
        """Best last rounds count scoring."""
        # Extract existing logic from EventView
        pass
```

**Impact:** Eliminates 400+ lines of duplication
**Effort:** 4-6 hours
**Files affected:** `views.py`, `views_stats/player_stats.py`, templates

---

### 1.3 Create Leaderboard Builder Service
**File:** `superb_ock/services/leaderboard.py`

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from django.db.models import QuerySet
from superb_ock.models import GolfEvent, Player, GolfRound, Score
from superb_ock.services.scoring import ScoringCalculator


@dataclass
class LeaderboardEntry:
    """Single player entry in leaderboard."""
    player: Player
    total_points: int
    round_scores: Dict[int, int]  # round_id -> points
    counting_rounds: List[int]
    rounds_played: int
    position: Optional[int] = None


class LeaderboardBuilder:
    """
    Builds leaderboards for events and homepage.
    Consolidates logic from Home and EventView.
    """

    def __init__(self, event: GolfEvent):
        self.event = event
        self.calculator = ScoringCalculator(event.scoring)

    def build(self) -> List[LeaderboardEntry]:
        """Build complete leaderboard with rankings."""
        entries = self._calculate_entries()
        entries = self._sort_entries(entries)
        entries = self._assign_positions(entries)
        return entries

    def _calculate_entries(self) -> List[LeaderboardEntry]:
        """Calculate scores for all players."""
        # Extract from Home.get_context() lines 164-195
        pass

    def _sort_entries(
        self,
        entries: List[LeaderboardEntry]
    ) -> List[LeaderboardEntry]:
        """Sort by total points descending."""
        return sorted(entries, key=lambda x: x.total_points, reverse=True)

    def _assign_positions(
        self,
        entries: List[LeaderboardEntry]
    ) -> List[LeaderboardEntry]:
        """Assign positions handling ties."""
        # Implement position assignment with tie handling
        pass

    def get_player_stats(self, player_id: int) -> Optional[LeaderboardEntry]:
        """Get stats for specific player."""
        entries = self.build()
        return next((e for e in entries if e.player.id == player_id), None)
```

**Impact:** Eliminates ~200 lines of duplication, makes leaderboard logic testable
**Effort:** 6-8 hours
**Files affected:** `views.py` (Home, EventView)

---

### 1.4 Create Media Processing Service
**File:** `superb_ock/services/media.py`

```python
from pathlib import Path
from typing import Tuple, List
import cv2
from PIL import Image, ImageEnhance
from superb_ock.constants import THUMBNAIL_QUALITY, PREVIEW_COUNT, PREVIEW_POSITIONS


class VideoThumbnailGenerator:
    """
    Handles video thumbnail and preview generation.
    Consolidates logic from admin.py and admin_views.py.
    """

    def __init__(self, video_path: Path):
        self.video_path = video_path

    def generate_thumbnail(self, output_path: Path) -> bool:
        """Generate thumbnail at video midpoint."""
        try:
            cap = cv2.VideoCapture(str(self.video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            mid_frame = total_frames // 2

            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            success, frame = cap.read()
            cap.release()

            if success:
                enhanced = self._enhance_image(frame)
                enhanced.save(output_path, 'JPEG', quality=THUMBNAIL_QUALITY)
                return True
            return False
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return False

    def generate_previews(self, output_dir: Path) -> List[Tuple[Path, float]]:
        """Generate preview images at 25%, 50%, 75% positions."""
        previews = []
        try:
            cap = cv2.VideoCapture(str(self.video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            for i, position in enumerate(PREVIEW_POSITIONS):
                frame_num = int(total_frames * position)
                timestamp = frame_num / fps if fps > 0 else 0

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                success, frame = cap.read()

                if success:
                    output_path = output_dir / f"{self.video_path.stem}_preview_{i}.jpg"
                    enhanced = self._enhance_image(frame)
                    enhanced.save(output_path, 'JPEG', quality=THUMBNAIL_QUALITY)
                    previews.append((output_path, timestamp))

            cap.release()
            return previews
        except Exception as e:
            print(f"Error generating previews: {e}")
            return []

    def _enhance_image(self, frame) -> Image:
        """Apply enhancement to video frame."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        # Apply enhancements
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)

        return image


class ImageProcessor:
    """General image processing utilities."""

    @staticmethod
    def resize_with_aspect_ratio(
        image: Image,
        max_width: int,
        max_height: int
    ) -> Image:
        """Resize image maintaining aspect ratio."""
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return image

    @staticmethod
    def optimize_for_web(image: Image, quality: int = 85) -> Image:
        """Optimize image for web delivery."""
        # Could add format conversion, compression, etc.
        return image
```

**Impact:** Eliminates ~150 lines of duplication, centralizes media logic
**Effort:** 3-4 hours
**Files affected:** `admin.py`, `admin_views.py`, management commands

---

## Phase 2: Improve Data Layer

### 2.1 Create Custom QuerySet Managers
**File:** `superb_ock/managers.py`

```python
from django.db import models
from django.db.models import Prefetch, Sum, Count


class ScoreQuerySet(models.QuerySet):
    """Custom queryset for Score model."""

    def for_round(self, round_id: int):
        """Get all scores for a specific round."""
        return self.filter(golf_round_id=round_id)

    def for_player(self, player_id: int):
        """Get all scores for a specific player."""
        return self.filter(player_id=player_id)

    def for_event(self, event_id: int):
        """Get all scores for an event."""
        return self.filter(golf_round__event_id=event_id)

    def with_related(self):
        """Eager load related objects."""
        return self.select_related(
            'player',
            'hole',
            'hole__golf_course',
            'golf_round'
        ).prefetch_related('highlight')

    def with_stableford_total(self):
        """Annotate with stableford total."""
        return self.aggregate(total=Sum('stableford'))['total'] or 0

    def with_highlights(self):
        """Only scores that have highlights."""
        return self.filter(highlight__isnull=False).distinct()

    def without_highlights(self):
        """Only scores without highlights."""
        return self.filter(highlight__isnull=True)


class GolfRoundQuerySet(models.QuerySet):
    """Custom queryset for GolfRound model."""

    def for_event(self, event_id: int):
        """Get all rounds for an event."""
        return self.filter(event_id=event_id)

    def with_scores(self):
        """Eager load all scores."""
        return self.prefetch_related(
            Prefetch('score_set', queryset=Score.objects.with_related())
        )

    def completed(self):
        """Get completed rounds (all 72 scores entered)."""
        return self.annotate(
            score_count=Count('score')
        ).filter(score_count=72)  # 4 players × 18 holes

    def by_date(self, ascending=True):
        """Order by date started."""
        order = 'date_started' if ascending else '-date_started'
        return self.order_by(order)


class HighlightQuerySet(models.QuerySet):
    """Custom queryset for Highlight model."""

    def with_previews(self):
        """Eager load preview images."""
        return self.prefetch_related('highlightpreview_set')

    def for_player(self, player_id: int):
        """Get highlights for a specific player."""
        return self.filter(score__player_id=player_id).distinct()

    def for_round(self, round_id: int):
        """Get highlights for a specific round."""
        return self.filter(score__golf_round_id=round_id).distinct()

    def with_video(self):
        """Only highlights with video files."""
        return self.exclude(video='')
```

**Update models.py:**
```python
class Score(models.Model):
    # ... existing fields ...

    objects = ScoreQuerySet.as_manager()


class GolfRound(models.Model):
    # ... existing fields ...

    objects = GolfRoundQuerySet.as_manager()


class Highlight(models.Model):
    # ... existing fields ...

    objects = HighlightQuerySet.as_manager()
```

**Impact:** Cleaner view code, reusable queries, better performance
**Effort:** 4-5 hours
**Files affected:** `models.py`, all views

---

### 2.2 Add Model Helper Methods
**Update:** `superb_ock/models.py`

```python
class GolfRound(models.Model):
    # ... existing fields ...

    def get_scores_for_player(self, player_id: int):
        """Get all scores for a player in this round."""
        return self.score_set.filter(player_id=player_id).order_by('hole__hole_number')

    def get_leaderboard(self):
        """Get leaderboard for this round."""
        from superb_ock.services.leaderboard import LeaderboardBuilder
        if self.event:
            builder = LeaderboardBuilder(self.event)
            return builder.build()
        return []

    def is_complete(self) -> bool:
        """Check if round has all scores entered."""
        return self.score_set.count() == 72  # 4 players × 18 holes

    @property
    def total_holes(self) -> int:
        """Total holes that should be played."""
        return 18  # Could come from constants


class Player(models.Model):
    # ... existing fields ...

    def get_recent_rounds(self, limit: int = 5):
        """Get player's most recent rounds."""
        return GolfRound.objects.filter(
            score__player=self
        ).distinct().order_by('-date_started')[:limit]

    def get_average_score(self) -> float:
        """Calculate average stableford score."""
        total = self.score_set.aggregate(
            total=Sum('stableford')
        )['total'] or 0
        count = self.score_set.count() or 1
        return total / count

    @property
    def full_name(self) -> str:
        """Get player's full name."""
        return f"{self.first_name} {self.second_name}"


class Score(models.Model):
    # ... existing fields ...

    def is_birdie(self) -> bool:
        """Check if score is a birdie."""
        return self.shots_taken < self.hole.par

    def is_eagle(self) -> bool:
        """Check if score is an eagle."""
        return self.shots_taken <= self.hole.par - 2

    def is_bogey(self) -> bool:
        """Check if score is a bogey."""
        return self.shots_taken == self.hole.par + 1

    def score_to_par(self) -> int:
        """Calculate score relative to par."""
        return self.shots_taken - self.hole.par
```

**Impact:** Cleaner template code, encapsulated business logic
**Effort:** 2-3 hours
**Files affected:** `models.py`, templates

---

## Phase 3: Add Type Safety

### 3.1 Add Type Hints Throughout
**Examples:**

```python
# views.py
from typing import Dict, List, Any, Optional
from django.http import HttpRequest, HttpResponse
from django.db.models import QuerySet

class Home(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        # ...

    def get_context(self, request: HttpRequest) -> Dict[str, Any]:
        # ...

def signUpUser(request: HttpRequest) -> HttpResponse:
    # ...

# services/scoring.py
from typing import List, Dict, Optional
from django.db.models import QuerySet

class ScoringCalculator:
    def calculate_total(
        self,
        scores: QuerySet[Score],
        player_id: int
    ) -> int:
        # ...
```

**Impact:** Better IDE support, catch bugs earlier, clearer intent
**Effort:** 8-10 hours (entire codebase)
**Files affected:** All Python files

---

## Phase 4: Improve Error Handling & Logging

### 4.1 Replace Print Statements with Logging
**File:** `superb_ock/logging_config.py`

```python
import logging
from pathlib import Path

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/golf2025.log'),
            logging.StreamHandler()
        ]
    )

# Create logger instances
logger = logging.getLogger('superb_ock')
media_logger = logging.getLogger('superb_ock.media')
notification_logger = logging.getLogger('superb_ock.notifications')
```

**Replace print statements:**
```python
# Before:
print(f"Error generating thumbnail: {e}")

# After:
media_logger.error(f"Error generating thumbnail for {video_path}: {e}", exc_info=True)
```

**Impact:** Better debugging, production monitoring
**Effort:** 3-4 hours
**Files affected:** All files with print statements

---

### 4.2 Add Comprehensive Error Handling
**Example for views:**

```python
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

class GolfRoundView(View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        try:
            golf_round = GolfRound.objects.get(id=pk)
        except ObjectDoesNotExist:
            logger.warning(f"Round {pk} not found (requested by {request.user})")
            raise Http404("Golf round not found")
        except Exception as e:
            logger.error(f"Unexpected error loading round {pk}: {e}", exc_info=True)
            return HttpResponse("An error occurred", status=500)

        # ... rest of logic
```

**Impact:** Better user experience, easier debugging
**Effort:** 4-6 hours
**Files affected:** All views

---

## Phase 5: Testing Infrastructure

### 5.1 Create Test Structure
**Files to create:**

```
superb_ock/tests/
├── __init__.py
├── test_models.py
├── test_views.py
├── test_services/
│   ├── __init__.py
│   ├── test_scoring.py
│   ├── test_leaderboard.py
│   └── test_media.py
├── test_forms.py
├── test_managers.py
└── fixtures/
    ├── courses.json
    ├── players.json
    └── rounds.json
```

**Example test:**
```python
# tests/test_services/test_scoring.py
from django.test import TestCase
from superb_ock.models import GolfEvent, Player, Score
from superb_ock.services.scoring import ScoringCalculator
from superb_ock.constants import ScoringFormat


class ScoringCalculatorTestCase(TestCase):
    fixtures = ['courses', 'players', 'rounds']

    def setUp(self):
        self.event = GolfEvent.objects.create(
            name="Test Event",
            scoring=ScoringFormat.BEST_THREE_OF_FIVE
        )
        self.calculator = ScoringCalculator(self.event.scoring)

    def test_calculate_best_three_of_five(self):
        """Test best 3 of 5 scoring calculation."""
        player = Player.objects.first()
        scores = Score.objects.filter(player=player)

        total = self.calculator.calculate_total(scores, player.id)

        self.assertIsInstance(total, int)
        self.assertGreaterEqual(total, 0)

    def test_counting_rounds_identification(self):
        """Test correct identification of counting rounds."""
        # ... test implementation
```

**Impact:** Confidence in refactoring, prevent regressions
**Effort:** 20-30 hours (comprehensive suite)
**Files affected:** New test files

---

### 5.2 Add pytest Configuration
**File:** `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = golf2025.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --reuse-db
    --cov=superb_ock
    --cov-report=html
    --cov-report=term-missing
```

**Add to requirements.txt:**
```
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
```

---

## Phase 6: Configuration Improvements

### 6.1 Environment-Based Configuration
**File:** `.env.example`

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Site
SITE_URL=http://localhost:8000

# VAPID Keys (for web push)
VAPID_PRIVATE_KEY_PATH=vapid_private.pem
VAPID_PUBLIC_KEY=your-public-key-here
VAPID_ADMIN_EMAIL=admin@example.com

# Media
MEDIA_ROOT=media/
MEDIA_URL=/media/

# Security (production)
CSRF_TRUSTED_ORIGINS=https://www.thesuperbock.co.uk
SECURE_SSL_REDIRECT=False
```

**Update settings.py:**
```python
import os
from pathlib import Path
from environs import Env

env = Env()
env.read_env()

SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

SITE_URL = env.str('SITE_URL', default='http://localhost:8000')
```

**Add to requirements.txt:**
```
environs==10.3.0
```

**Impact:** Secure configuration, easy deployment, no hardcoded secrets
**Effort:** 2-3 hours
**Files affected:** `settings.py`, deployment

---

## Phase 7: Performance Optimizations

### 7.1 Add Caching
**Update settings.py:**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env.str('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'golf2025',
        'TIMEOUT': 300,  # 5 minutes default
    }
}
```

**Add caching to expensive views:**
```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache 5 minutes
class HeatMap(View):
    # ...
```

**Cache leaderboard calculations:**
```python
from django.core.cache import cache

class LeaderboardBuilder:
    def build(self) -> List[LeaderboardEntry]:
        cache_key = f'leaderboard_{self.event.id}'
        cached = cache.get(cache_key)

        if cached:
            return cached

        entries = self._calculate_entries()
        # ... build logic

        cache.set(cache_key, entries, timeout=300)  # 5 minutes
        return entries
```

**Impact:** Faster page loads, reduced database queries
**Effort:** 4-6 hours
**Files affected:** `settings.py`, views, services

---

### 7.2 Add Pagination
**Example:**

```python
from django.core.paginator import Paginator

class RoundsOverview(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        all_rounds = GolfRound.objects.all().by_date(ascending=False)

        paginator = Paginator(all_rounds, 25)  # 25 rounds per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # ... group logic

        context = {
            'page_obj': page_obj,
            'grouped_rounds': grouped_rounds,
        }
        return render(request, 'superb_ock/rounds/overview.html', context)
```

**Impact:** Better performance with large datasets
**Effort:** 2-3 hours
**Files affected:** `views.py` (RoundsOverview, HighlightsView)

---

## Phase 8: Code Organization

### 8.1 Split Large Files
**Create structure:**

```
superb_ock/views/
├── __init__.py              # Import all views for backwards compatibility
├── homepage.py              # Home view
├── rounds.py                # NewRound, RoundsOverview, GolfRoundView
├── scores.py                # EditScore
├── highlights.py            # HighlightsView
├── events.py                # EventView
├── auth.py                  # signUpUser, logInUser, logOutUser
└── visualizations.py        # HeatMap

superb_ock/views_stats/
├── __init__.py
├── stats.py                 # heatmap_data
├── players.py               # player stats views
└── courses.py               # course stats views
```

**Impact:** Easier navigation, better organization
**Effort:** 3-4 hours
**Files affected:** `views.py` → multiple files, `urls.py` updates

---

### 8.2 Create Services Directory
**Structure:**

```
superb_ock/services/
├── __init__.py
├── scoring.py               # ScoringCalculator
├── leaderboard.py           # LeaderboardBuilder
├── media.py                 # VideoThumbnailGenerator, ImageProcessor
└── notifications.py         # Notification logic (extract from notifications.py)
```

---

## Implementation Timeline

### Sprint 1 (Week 1): Foundation
- [ ] Create constants.py
- [ ] Add type hints to models
- [ ] Create logging configuration
- [ ] Set up environment-based config

**Effort:** 12-15 hours

---

### Sprint 2 (Week 2): Core Services
- [ ] Create ScoringCalculator service
- [ ] Create LeaderboardBuilder service
- [ ] Update Home view to use services
- [ ] Update EventView to use services

**Effort:** 15-20 hours

---

### Sprint 3 (Week 3): Media & Data Layer
- [ ] Create VideoThumbnailGenerator service
- [ ] Create custom QuerySet managers
- [ ] Add model helper methods
- [ ] Update admin.py and admin_views.py

**Effort:** 10-15 hours

---

### Sprint 4 (Week 4): Testing & Quality
- [ ] Set up pytest infrastructure
- [ ] Write tests for services
- [ ] Write tests for models
- [ ] Write tests for views

**Effort:** 20-25 hours

---

### Sprint 5 (Week 5): Performance & Polish
- [ ] Add caching
- [ ] Add pagination
- [ ] Split large view files
- [ ] Comprehensive error handling

**Effort:** 10-15 hours

---

## Success Metrics

1. **Code Duplication:** Reduce from ~500 lines to <50 lines
2. **Test Coverage:** From 0% to 70%+
3. **Type Hints:** From 0% to 90%+
4. **Largest File:** Reduce views.py from 1182 lines to <300 lines
5. **Query Performance:** Reduce average page load by 30%+

---

## Risks & Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Create comprehensive tests BEFORE refactoring
- Use feature flags for gradual rollout
- Keep backup of working code

### Risk 2: Time Investment
**Mitigation:**
- Implement in sprints with deliverables
- Prioritize high-impact changes first
- Can pause between sprints

### Risk 3: Database Changes
**Mitigation:**
- Most changes don't require migrations
- Test migrations thoroughly in development
- Keep database backups

---

## Notes

- This plan is incremental - each phase delivers value
- Can be done over 5 weeks part-time or 1-2 weeks full-time
- Prioritize Phase 1 & 2 for biggest impact
- Test coverage is critical before refactoring
