from django.contrib.auth.models import User
from .models import UserProfile, PushDevice
import json

def get_absolute_icon_url():
    """Get absolute URL for notification icon"""
    from django.conf import settings

    # Get base URL from settings or use localhost for development
    if hasattr(settings, 'SITE_URL'):
        base_url = settings.SITE_URL
    else:
        # Use http for local development, https for production
        protocol = 'http' if settings.DEBUG else 'https'
        # Try to get domain from ALLOWED_HOSTS
        if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != '*':
            domain = settings.ALLOWED_HOSTS[0]
        else:
            domain = 'localhost:8000'
        base_url = f"{protocol}://{domain}"

    return f"{base_url}/static/superb_ock/images/logo.png"

def send_to_user_devices(user, payload):
    """Send notification to all active devices for a user"""
    devices = PushDevice.objects.filter(user=user, is_active=True)
    print(f"[NOTIFICATION] Sending to {devices.count()} device(s) for {user.username}")

    sent_count = 0
    for device in devices:
        if device.subscription_info:
            try:
                # Use pywebpush to send to this specific subscription
                from pywebpush import webpush
                from django.conf import settings

                subscription_info = {
                    'endpoint': device.subscription_info.endpoint,
                    'keys': {
                        'p256dh': device.subscription_info.p256dh,
                        'auth': device.subscription_info.auth,
                    }
                }

                vapid_claims = {
                    "sub": f"mailto:{settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}"
                }

                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
                    vapid_claims=vapid_claims,
                    ttl=1000
                )
                sent_count += 1
                print(f"[NOTIFICATION] Sent to device: {device.device_name}")
            except Exception as e:
                print(f"[NOTIFICATION] Failed to send to device {device.device_name}: {e}")
                import traceback
                traceback.print_exc()

    return sent_count

def send_round_start_notification(golf_round):
    """Send notification when a new round starts"""
    # Send to users with notifications enabled and round start preference
    profiles = UserProfile.objects.filter(
        notifications_enabled=True,
        notify_round_start=True
    )
    print(f"[NOTIFICATION] Round started - sending to {profiles.count()} users")

    icon_url = get_absolute_icon_url()

    for profile in profiles:
        payload = {
            'head': 'Round Started!',
            'body': f'New round for {golf_round.event.name}',
            'icon': icon_url,
            'url': f'/rounds/{golf_round.id}',
        }

        try:
            send_to_user_devices(profile.user, payload)
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send to {profile.user.username}: {e}")

def send_hole_completed_notification(score, player_total=None):
    """Send notification when a hole is completed"""
    print(f"[NOTIFICATION] Hole completed - shots_taken: {score.shots_taken}, hole: {score.hole}")

    # Send to users with notifications enabled and hole completed preference
    profiles = UserProfile.objects.filter(
        notifications_enabled=True,
        notify_hole_completed=True
    )
    print(f"[NOTIFICATION] Found {profiles.count()} users with notifications enabled")

    icon_url = get_absolute_icon_url()

    for profile in profiles:
        # Build notification text
        player_name = f"{score.player.first_name} {score.player.second_name}"
        hole_num = score.hole.hole_number
        shots = score.shots_taken
        par = score.hole.par
        points = score.stableford

        # Title: "Hole 5 - John Smith"
        title = f"Hole {hole_num} - {player_name}"

        # Body: "4 on par 3 • 3pts • Total: 18pts"
        diff = shots - par
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "Par"

        body_parts = [f"{shots} ({diff_str})"]
        if points is not None:
            body_parts.append(f"{points}pts")
        if player_total is not None:
            body_parts.append(f"Total: {player_total}pts")

        body = " • ".join(body_parts)

        payload = {
            'head': title[:40],  # Limit to 40 chars for safety
            'body': body[:120],  # Limit to 120 chars for safety
            'icon': icon_url,
            'url': f'/rounds/{score.golf_round.id}',
        }

        try:
            send_to_user_devices(profile.user, payload)
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send to {profile.user.username}: {e}")

def send_round_completed_notification(golf_round):
    """Send notification when a round is completed"""
    # Send to users with notifications enabled and round completed preference
    profiles = UserProfile.objects.filter(
        notifications_enabled=True,
        notify_round_completed=True
    )
    print(f"[NOTIFICATION] Round completed - sending to {profiles.count()} users")

    icon_url = get_absolute_icon_url()

    for profile in profiles:
        payload = {
            'head': 'Round Completed!',
            'body': f'{golf_round.event.name} is finished',
            'icon': icon_url,
            'url': f'/rounds/{golf_round.id}',
        }

        try:
            send_to_user_devices(profile.user, payload)
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send to {profile.user.username}: {e}")