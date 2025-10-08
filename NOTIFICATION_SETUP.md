# Web Push Notifications Setup Guide

## Overview
This guide explains how to set up and debug web push notifications in the golf2025 Django application.

## Architecture

### Components
1. **Django Backend** - Sends notifications via webpush library
2. **Service Worker** - Receives and displays browser notifications
3. **VAPID Keys** - Authentication for push notifications
4. **FCM (Firebase Cloud Messaging)** - Google's push notification service

## Current Status

### ✅ What's Working
- VAPID keys generated and configured
- Push subscriptions are saved to database
- Notifications are being sent successfully to FCM (HTTP 201 response)
- Service worker is registered

### ❌ What's Not Working
- Browser is not receiving/displaying the notifications

## Debugging Steps

### 1. Check Service Worker
Open Chrome DevTools → Application → Service Workers

**What to check:**
- Is the service worker "activated and running"?
- Status should be green
- Source should be `/static/superb_ock/js/sw.js`

**To force update:**
```
1. Click "Unregister" on the service worker
2. Hard refresh the page (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
3. Service worker should re-register automatically
```

### 2. Check Browser Console for Service Worker Logs
When you click "Test Notification", you should see logs like:
```
[SW] Push event received
[SW] Event has data
[SW] Parsed data: {head: "Test Notification", body: "...", ...}
[SW] Showing notification: Test Notification
```

**If you DON'T see these logs:**
- The push message is not reaching the service worker
- This could be a browser/FCM issue

### 3. Check Notification Permissions
```javascript
// Run this in browser console:
console.log(Notification.permission); // Should be "granted"
```

If it's "denied", you need to:
1. Click the lock icon in address bar
2. Allow notifications
3. Refresh and re-subscribe

### 4. Check Push Subscription
```javascript
// Run this in browser console:
navigator.serviceWorker.ready.then(reg => {
  reg.pushManager.getSubscription().then(sub => {
    console.log('Subscription:', sub);
  });
});
```

Should show an endpoint starting with `https://fcm.googleapis.com/...`

## Common Issues and Solutions

### Issue 1: Service Worker Not Receiving Push Events

**Possible causes:**
- Service worker scope issues
- Browser caching old service worker
- FCM endpoint issues

**Solution:**
```javascript
// 1. Unregister all service workers
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.unregister());
});

// 2. Clear site data
// DevTools → Application → Clear site data → Clear all

// 3. Reload and re-subscribe
```

### Issue 2: Notifications Not Showing Despite Service Worker Receiving Them

**Check:**
1. Browser notification settings (System Settings → Notifications)
2. Do Not Disturb mode
3. Focus Assist (Windows)

**Test with manual notification:**
```javascript
// Run in console on notifications page:
new Notification('Manual Test', {
  body: 'If you see this, notifications work',
  icon: '/static/superb_ock/images/logo.png'
});
```

### Issue 3: VAPID Key Mismatch

**Symptoms:**
- "Invalid application server key" errors
- Subscription fails

**Solution:**
Regenerate keys:
```bash
# In project root
python manage.py shell
>>> from py_vapid import Vapid
>>> vapid = Vapid()
>>> vapid.generate_keys()
>>> vapid.save_key('vapid_private.pem')
>>> vapid.save_public_key('vapid_public.pem')
>>>
>>> # Get the public key for settings.py
>>> from cryptography.hazmat.primitives import serialization
>>> public_key_bytes = vapid.public_key.public_bytes(
...     encoding=serialization.Encoding.X962,
...     format=serialization.PublicFormat.UncompressedPoint
... )
>>> import base64
>>> base64url = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
>>> print(base64url)
```

Update `settings.py` with the new base64url key.

## Manual Testing

### Test 1: Direct Service Worker Notification
```javascript
// Open DevTools Console
navigator.serviceWorker.ready.then(reg => {
  reg.showNotification('Direct Test', {
    body: 'Testing service worker directly',
    icon: '/static/superb_ock/images/logo.png'
  });
});
```

**Expected:** Notification appears immediately
**If it doesn't work:** Service worker or browser permissions issue

### Test 2: Simulated Push Event
```javascript
// This won't work due to browser security, but shows the concept
navigator.serviceWorker.ready.then(reg => {
  const data = JSON.stringify({
    head: 'Simulated Push',
    body: 'Testing push event',
    icon: '/static/superb_ock/images/logo.png',
    url: '/'
  });

  // Note: You can't actually trigger this from console
  // Real push events must come from push service
});
```

### Test 3: Backend Notification Send
```python
# Django shell
python manage.py shell

from django.contrib.auth.models import User
from webpush import send_user_notification
import json

user = User.objects.get(username='richardlongdon')

payload = {
    'head': 'Shell Test',
    'body': 'Testing from Django shell',
    'icon': '/static/superb_ock/images/logo.png',
    'url': '/'
}

# Send notification
send_user_notification(user=user, payload=json.dumps(payload), ttl=1000)
```

**Expected:** Browser notification appears
**Check server logs for:** HTTP 201 response to FCM

## Useful Resources

### Official Documentation
- [Web Push Protocol](https://web.dev/push-notifications-overview/)
- [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [django-webpush](https://github.com/safwanrahman/django-webpush)
- [Web Push Notifications Tutorial](https://developers.google.com/web/fundamentals/push-notifications)

### Testing Tools
- [Web Push Testing Tool](https://web-push-codelab.glitch.me/) - Test push notifications
- [VAPID Key Generator](https://vapidkeys.com/) - Generate VAPID keys online

### Debugging Tools
- Chrome DevTools → Application → Service Workers
- Chrome DevTools → Application → Storage → IndexedDB
- `chrome://serviceworker-internals/` - Advanced service worker debugging

## Alternative Approach: Using Firebase Directly

If web push continues to have issues, consider using Firebase Cloud Messaging SDK directly:

### Steps:
1. Create a Firebase project at https://console.firebase.google.com/
2. Get your Firebase config
3. Install Firebase JavaScript SDK
4. Use Firebase messaging instead of generic web push

### Benefits:
- Better debugging tools in Firebase console
- More reliable delivery
- Better mobile support
- Message history and analytics

### Implementation:
```html
<!-- Add to base.html -->
<script src="https://www.gstatic.com/firebasejs/9.0.0/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging.js"></script>
<script>
  // Firebase configuration
  const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    projectId: "YOUR_PROJECT_ID",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
  };

  firebase.initializeApp(firebaseConfig);
  const messaging = firebase.messaging();

  // Request permission and get token
  messaging.requestPermission()
    .then(() => messaging.getToken())
    .then(token => {
      console.log('FCM Token:', token);
      // Send token to your server
    });
</script>
```

## Current Implementation Files

### Backend
- `superb_ock/models.py` - UserProfile model
- `superb_ock/views_notifications.py` - Notification views
- `superb_ock/notifications.py` - Notification sending logic
- `superb_ock/urls.py` - Notification URL patterns
- `golf2025/settings.py` - VAPID configuration

### Frontend
- `superb_ock/templates/superb_ock/base.html` - Service worker registration
- `superb_ock/templates/superb_ock/notifications.html` - Settings page
- `superb_ock/static/superb_ock/js/sw.js` - Service worker

### Database
- `webpush_pushinformation` - Links users to subscriptions
- `webpush_subscriptioninfo` - Stores push subscription details

## Next Steps

1. **Verify basic notifications work** - Use Test 1 above
2. **Check service worker receives push events** - Look for `[SW]` logs
3. **If still not working** - Consider Firebase alternative
4. **Test on different browsers** - Chrome, Firefox, Edge
5. **Test on mobile** - Android Chrome, iOS Safari (limited support)

## Contact for Help

If you need further assistance:
- Django-webpush issues: https://github.com/safwanrahman/django-webpush/issues
- Web Push spec: https://github.com/w3c/push-api
- MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/API/Push_API
