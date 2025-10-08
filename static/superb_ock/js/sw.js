// Service Worker for Push Notifications
self.addEventListener('install', function(event) {
    console.log('Service Worker installing');
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activating');
});

self.addEventListener('push', function(event) {
    console.log('[SW] Push event received', event);

    if (event.data) {
        console.log('[SW] Event has data');
        try {
            let payload = event.data.json();
            console.log('[SW] Initial parse:', payload, typeof payload);

            // If it's a string, parse it again
            if (typeof payload === 'string') {
                payload = JSON.parse(payload);
                console.log('[SW] Double parsed:', payload);
            }

            const options = {
                body: payload.body,
                icon: payload.icon || '/static/superb_ock/images/logo.png',
                badge: '/static/superb_ock/images/logo.png',
                vibrate: [200, 100, 200],
                data: {
                    url: payload.url
                }
            };

            console.log('[SW] Showing notification:', payload.head, options);
            event.waitUntil(
                self.registration.showNotification(payload.head, options)
            );
        } catch (e) {
            console.error('[SW] Error parsing push data:', e);
            console.log('[SW] Raw data:', event.data.text());
        }
    } else {
        console.log('[SW] No data in push event');
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.notification.data && event.notification.data.url) {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});