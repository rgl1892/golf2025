from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import UserProfile, PushDevice
import json

@login_required
@ensure_csrf_cookie
def notifications_settings(request):
    """Display notification settings page"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Get user's devices
    devices = PushDevice.objects.filter(user=request.user)

    context = {
        'webpush_settings': settings.WEBPUSH_SETTINGS,
        'notifications_enabled': profile.notifications_enabled,
        'notify_round_start': profile.notify_round_start,
        'notify_hole_completed': profile.notify_hole_completed,
        'notify_round_completed': profile.notify_round_completed,
        'devices': devices,
    }
    return render(request, 'superb_ock/notifications.html', context)

@login_required
@require_POST
def toggle_notifications(request):
    """Toggle user notification preference"""
    print(f"[TOGGLE] User: {request.user.username}, Method: {request.method}")
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.notifications_enabled = not profile.notifications_enabled
        profile.save()
        print(f"[TOGGLE] Saved: enabled={profile.notifications_enabled}")
        return JsonResponse({'enabled': profile.notifications_enabled})
    except Exception as e:
        print(f"[TOGGLE] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def test_notification(request):
    """Send test notification to all user devices"""
    from .notifications import send_to_user_devices, get_absolute_icon_url

    payload = {
        'head': 'Test Notification',
        'body': 'This is a test notification from golf2025',
        'icon': get_absolute_icon_url(),
        'url': '/',
    }

    try:
        # Check if user has any devices
        device_count = PushDevice.objects.filter(user=request.user, is_active=True).count()
        if device_count == 0:
            print(f"[NOTIFICATION TEST] No active devices for user {request.user.username}")
            return JsonResponse({'error': 'No active devices found. Please enable notifications first.'}, status=400)

        print(f"[NOTIFICATION TEST] Sending to {device_count} device(s) for {request.user.username}")
        print(f"[NOTIFICATION TEST] Payload: {payload}")

        sent_count = send_to_user_devices(request.user, payload)
        print(f"[NOTIFICATION TEST] Successfully sent to {sent_count}/{device_count} device(s)")

        # Get list of devices for display
        devices = PushDevice.objects.filter(user=request.user, is_active=True)
        device_list = [{'name': d.device_name, 'browser': d.browser} for d in devices]

        return JsonResponse({
            'status': 'sent',
            'devices': device_count,
            'sent': sent_count,
            'device_list': device_list
        })
    except Exception as e:
        print(f"[NOTIFICATION TEST] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_subscription(request):
    """Save push notification subscription"""
    from webpush.models import SubscriptionInfo
    import logging
    logger = logging.getLogger('superb_ock.notifications')

    try:
        data = json.loads(request.body)
        logger.info(f"[SUBSCRIPTION] Received data from {request.user.username}: {data.keys() if data else 'None'}")

        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')
        device_name = data.get('device_name', 'Unknown Device')

        if not all([endpoint, p256dh, auth]):
            logger.warning(f"[SUBSCRIPTION] Missing required fields - endpoint: {bool(endpoint)}, p256dh: {bool(p256dh)}, auth: {bool(auth)}")
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        logger.info(f"[SUBSCRIPTION] Creating/updating subscription for endpoint: {endpoint[:50]}...")

        # Check if subscription already exists, update if it does
        sub_info, sub_created = SubscriptionInfo.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'browser': 'CHROME',
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
                'p256dh': p256dh,
                'auth': auth,
            }
        )
        logger.info(f"[SUBSCRIPTION] SubscriptionInfo {'created' if sub_created else 'updated'} - ID: {sub_info.id}")

        # Detect browser from user agent (order matters - check most specific first)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        browser = 'Unknown'
        if 'Edg' in user_agent or 'Edge' in user_agent:
            browser = 'Edge'
        elif 'OPR' in user_agent or 'Opera' in user_agent:
            browser = 'Opera'
        elif 'Chrome' in user_agent and 'Safari' in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent:
            browser = 'Safari'

        # Use update_or_create to handle the OneToOneField constraint
        # The subscription_info is unique, so we can use it as the lookup
        device, device_created = PushDevice.objects.update_or_create(
            subscription_info=sub_info,
            defaults={
                'user': request.user,
                'device_name': device_name,
                'browser': browser,
                'user_agent': user_agent,
                'is_active': True,
            }
        )

        if device_created:
            logger.info(f"[SUBSCRIPTION] Created new device '{device.device_name}' for user {request.user.username}")
        else:
            logger.info(f"[SUBSCRIPTION] Updated existing device '{device.device_name}' for user {request.user.username}")

        return JsonResponse({'status': 'success', 'device_id': device.id}, status=201)

    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def toggle_device(request):
    """Toggle device active status"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')

        device = PushDevice.objects.get(id=device_id, user=request.user)
        device.is_active = not device.is_active
        device.save()

        print(f"[DEVICE] Toggled device {device.device_name} to {device.is_active}")
        return JsonResponse({'is_active': device.is_active})

    except PushDevice.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    except Exception as e:
        print(f"[DEVICE] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def delete_device(request):
    """Delete a device"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')

        device = PushDevice.objects.get(id=device_id, user=request.user)
        device_name = device.device_name
        device.delete()

        print(f"[DEVICE] Deleted device {device_name}")
        return JsonResponse({'status': 'deleted'})

    except PushDevice.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    except Exception as e:
        print(f"[DEVICE] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_preferences(request):
    """Update notification preferences"""
    try:
        data = json.loads(request.body)
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Update preferences
        if 'notify_round_start' in data:
            profile.notify_round_start = data['notify_round_start']
        if 'notify_hole_completed' in data:
            profile.notify_hole_completed = data['notify_hole_completed']
        if 'notify_round_completed' in data:
            profile.notify_round_completed = data['notify_round_completed']

        profile.save()

        print(f"[PREFERENCES] Updated for {request.user.username}: round_start={profile.notify_round_start}, hole_completed={profile.notify_hole_completed}, round_completed={profile.notify_round_completed}")
        return JsonResponse({
            'notify_round_start': profile.notify_round_start,
            'notify_hole_completed': profile.notify_hole_completed,
            'notify_round_completed': profile.notify_round_completed,
        })

    except Exception as e:
        print(f"[PREFERENCES] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)