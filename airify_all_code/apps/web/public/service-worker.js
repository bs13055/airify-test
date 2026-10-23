/**
 * Airify Service Worker — local asset caching only.
 * No push notifications. No background location. No third-party scripts.
 * API calls are NOT cached (always network-first).
 */
const CACHE_NAME = 'airify-v1-static';
const SCOPE_PATH = new URL(self.registration.scope).pathname;
const STATIC_ASSETS = [SCOPE_PATH, SCOPE_PATH + 'index.html'];

self.addEventListener('install', function (event) {
    event.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)));
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))));
    self.clients.claim();
});

self.addEventListener('fetch', function (event) {
    const url = new URL(event.request.url);
    if (url.pathname.startsWith('/v1/') || url.pathname === '/healthz' || url.pathname === '/version') {
        event.respondWith(fetch(event.request));
        return;
    }
    event.respondWith(caches.match(event.request).then(c => c || fetch(event.request)));
});
