from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import UserProfile

@login_required
@ensure_csrf_cookie
def notifications_settings(request):
    """Display notification settings page"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'webpush_settings': settings.WEBPUSH_SETTINGS,
        'notifications_enabled': profile.notifications_enabled
    }
    return render(request, 'superb_ock/notifications.html', context)

@login_required
@require_POST
def toggle_notifications(request):
    """Toggle user notification preference"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.notifications_enabled = not profile.notifications_enabled
    profile.save()

    return JsonResponse({'enabled': profile.notifications_enabled})

@login_required
@require_POST
def test_notification(request):
    """Send test notification"""
    from webpush import send_user_notification
    from webpush.models import PushInformation

    payload = {
        'head': 'Test Notification',
        'body': 'This is a test notification from golf2025',
        'icon': '/static/superb_ock/images/logo.png',
        'url': '/',
    }

    try:
        # Check if user has push info
        push_info = PushInformation.objects.filter(user=request.user).first()
        if not push_info:
            print(f"[NOTIFICATION TEST] No PushInformation for user {request.user.username}")
            return JsonResponse({'error': 'No push subscription found. Please enable notifications first.'}, status=400)

        if not push_info.subscription:
            print(f"[NOTIFICATION TEST] No subscription for user {request.user.username}")
            return JsonResponse({'error': 'No subscription found. Please toggle notifications off and on again.'}, status=400)

        print(f"[NOTIFICATION TEST] Sending to {request.user.username}")
        print(f"[NOTIFICATION TEST] Endpoint: {push_info.subscription.endpoint[:50]}...")
        print(f"[NOTIFICATION TEST] Payload: {payload}")

        import json
        result = send_user_notification(user=request.user, payload=json.dumps(payload), ttl=1000)
        print(f"[NOTIFICATION TEST] Send result: {result}")

        return JsonResponse({'status': 'sent', 'result': str(result)})
    except Exception as e:
        print(f"[NOTIFICATION TEST] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def save_subscription(request):
    """Save push notification subscription"""
    import json
    from webpush.models import PushInformation, SubscriptionInfo

    try:
        data = json.loads(request.body)
        print(f"[SUBSCRIPTION] Received data: {data}")

        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not all([endpoint, p256dh, auth]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

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

        # Get or create PushInformation for user with this subscription
        push_info, push_created = PushInformation.objects.update_or_create(
            user=request.user,
            defaults={'subscription': sub_info}
        )

        print(f"[SUBSCRIPTION] Saved for user {request.user.username} (sub_created={sub_created}, push_created={push_created})")
        return JsonResponse({'status': 'success'}, status=201)

    except Exception as e:
        print(f"[SUBSCRIPTION] Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)