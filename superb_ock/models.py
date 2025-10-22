from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import (
    HOLES_PER_ROUND,
    MAX_PLAYERS_PER_ROUND,
    ScoringFormat,
    Handedness,
    CarouselSettings,
    NotificationSettings,
)
from .managers import ScoreManager, GolfRoundManager, HighlightManager


# Create your models here.

class CarouselImage(models.Model):
    title = models.CharField(max_length=100, help_text="Title displayed on the image")
    description = models.TextField(max_length=200, help_text="Description displayed on the image")
    image = models.ImageField(upload_to='carousel/', help_text="Upload carousel image")
    order = models.PositiveIntegerField(
        default=CarouselSettings.DEFAULT_ORDER,
        help_text="Display order (lower numbers first)"
    )
    is_active = models.BooleanField(default=True, help_text="Show this image in the carousel")

    # Focal point controls (0-100 percentage)
    focal_point_x = models.PositiveIntegerField(
        default=CarouselSettings.DEFAULT_FOCAL_POINT_X,
        help_text="Horizontal focal point (0=left, 50=center, 100=right)"
    )
    focal_point_y = models.PositiveIntegerField(
        default=CarouselSettings.DEFAULT_FOCAL_POINT_Y,
        help_text="Vertical focal point (0=top, 50=center, 100=bottom)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Carousel Image"
        verbose_name_plural = "Carousel Images"
    
    def __str__(self):
        return f"{self.title} (Order: {self.order})"

def hole_choice():
    """Generate choices for hole numbers (1-18)."""
    return [(x + 1, f'{x + 1}') for x in range(HOLES_PER_ROUND)]

class GolfCourse(models.Model):
    
    name = models.CharField(max_length=20)
    country = models.CharField(max_length=20,null=True)
    tees = models.CharField(max_length=20,default='White')
    slope_rating = models.IntegerField(default=113)
    course_rating = models.FloatField(default=72)
    par = models.IntegerField(default=72)
    slug = models.SlugField(default="", null=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.tees} Tees"

class GolfEvent(models.Model):

    name = models.CharField(max_length=40)
    scoring = models.TextField(
        max_length=40,
        choices=ScoringFormat.CHOICES,
        default=ScoringFormat.BEST_THREE_OF_FIVE
    )

    def __str__(self):
        return self.name

class GolfRound(models.Model):

    event = models.ForeignKey(GolfEvent,on_delete=models.CASCADE,default=1)
    date_started = models.DateField(blank=True,null=True)

    # Custom manager for optimized queries
    objects = GolfRoundManager()

    class Meta:
        indexes = [
            models.Index(fields=['-date_started'], name='idx_round_date'),
            models.Index(fields=['event', '-date_started'], name='idx_round_event_date'),
        ]
        ordering = ['-date_started']

    def __str__(self):
        return f"{self.event} - {self.pk}"

class Hole(models.Model):

    hole_number = models.IntegerField(choices=hole_choice())
    golf_course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE, null=True)  # tees implied by choice
    par = models.IntegerField(
        choices=[(3, '3'), (4, '4'), (5, '5')],
        default=4
    )
    yards = models.IntegerField(default=400)
    stroke_index = models.IntegerField(choices=hole_choice(), default=1)

    def __str__(self):
        return f"{self.golf_course} - Hole {self.hole_number}"

class Player(models.Model):

    first_name = models.CharField(max_length=20, null=True)
    second_name = models.CharField(max_length=20, null=True)
    ocks = models.IntegerField(default=0)
    handedness = models.CharField(
        max_length=20,
        choices=Handedness.CHOICES,
        default=Handedness.RIGHT
    )
    picture = models.ImageField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f"{self.first_name} {self.second_name}"
    
class Highlight(models.Model):
    title = models.CharField(max_length=40)
    video = models.FileField(upload_to='highlights')
    thumbnail = models.ImageField(blank=True, upload_to='highlights/thumbnails')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    # Custom manager for optimized queries
    objects = HighlightManager()

    class Meta:
        indexes = [
            models.Index(fields=['-created_at'], name='idx_highlight_created'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class HighlightPreview(models.Model):
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='previews')
    image = models.ImageField(upload_to='highlights/previews')
    timestamp = models.FloatField(help_text="Timestamp in seconds where this preview was captured")
    order = models.PositiveIntegerField(default=0, help_text="Display order (0=first, 1=second, 2=third)")
    
    class Meta:
        ordering = ['order']
        unique_together = [['highlight', 'order']]
    
    def __str__(self):
        return f"{self.highlight.title} - Preview {self.order + 1}"

class Score(models.Model):

    shots_taken = models.IntegerField(blank=True,null=True)
    stableford = models.IntegerField(blank=True,null=True)
    hole = models.ForeignKey(Hole,on_delete=models.CASCADE,null=True)
    player = models.ForeignKey(Player,on_delete=models.CASCADE,null=True)
    golf_round = models.ForeignKey(GolfRound,on_delete=models.CASCADE,null=True)
    handicap_index = models.FloatField()
    sandy = models.BooleanField(default=False)
    highlight = models.ManyToManyField(Highlight,blank=True)

    # Custom manager for optimized queries
    objects = ScoreManager()

    class Meta:
        indexes = [
            models.Index(fields=['golf_round', 'hole'], name='idx_score_round_hole'),
            models.Index(fields=['golf_round', 'player'], name='idx_score_round_player'),
        ]

    def __str__(self):
        return f"{self.player} {self.hole} {self.golf_round}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    notifications_enabled = models.BooleanField(default=NotificationSettings.DEFAULT_ENABLED)

    # Notification preferences
    notify_round_start = models.BooleanField(
        default=NotificationSettings.DEFAULT_NOTIFY_ROUND_START,
        help_text="Notify when a new round starts"
    )
    notify_hole_completed = models.BooleanField(
        default=NotificationSettings.DEFAULT_NOTIFY_HOLE_COMPLETED,
        help_text="Notify when you complete a hole"
    )
    notify_round_completed = models.BooleanField(
        default=NotificationSettings.DEFAULT_NOTIFY_ROUND_COMPLETED,
        help_text="Notify when a round is completed"
    )

    def __str__(self):
        return f"{self.user.username} - Notifications: {self.notifications_enabled}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class PushDevice(models.Model):
    """Represents a device registered for push notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_devices')
    subscription_info = models.OneToOneField('webpush.SubscriptionInfo', on_delete=models.CASCADE, null=True, blank=True)

    # Device identification
    device_name = models.CharField(max_length=100, help_text="User-friendly device name (e.g., 'iPhone', 'Chrome on Laptop')")
    browser = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    # Active status
    is_active = models.BooleanField(default=True, help_text="Enable/disable notifications for this device")

    class Meta:
        ordering = ['-last_used']

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"