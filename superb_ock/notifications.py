from webpush import send_user_notification
from django.contrib.auth.models import User
from .models import UserProfile
import json

def send_round_start_notification(golf_round):
    """Send notification when a new round starts"""
    # Send to users with notifications enabled
    profiles = UserProfile.objects.filter(notifications_enabled=True)
    print(f"[NOTIFICATION] Round started - sending to {profiles.count()} users")

    for profile in profiles:
        payload = {
            'head': 'Round Started!',
            'body': f'New round for {golf_round.event.name}',
            'icon': '/static/superb_ock/images/logo.png',
            'url': f'/rounds/{golf_round.id}',
        }

        try:
            send_user_notification(user=profile.user, payload=json.dumps(payload), ttl=1000)
            print(f"[NOTIFICATION] Sent to {profile.user.username}")
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send to {profile.user.username}: {e}")

def send_hole_completed_notification(score):
    """Send notification when a hole is completed"""
    print(f"[NOTIFICATION] Hole completed - shots_taken: {score.shots_taken}, hole: {score.hole}")

    # Send to users with notifications enabled
    profiles = UserProfile.objects.filter(notifications_enabled=True)
    print(f"[NOTIFICATION] Found {profiles.count()} users with notifications enabled")

    for profile in profiles:
        payload = {
            'head': f'Hole {score.hole.hole_number} Complete!',
            'body': f'Score: {score.shots_taken} on par {score.hole.par}',
            'icon': '/static/superb_ock/images/logo.png',
            'url': f'/rounds/{score.golf_round.id}',
        }

        try:
            send_user_notification(user=profile.user, payload=json.dumps(payload), ttl=1000)
            print(f"[NOTIFICATION] Sent to {profile.user.username}")
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send to {profile.user.username}: {e}")