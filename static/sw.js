const CACHE_NAME = 'medilensai-offline-v3';
const STATIC_ASSETS = [
  '/',
  '/login',
  '/offline',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/charts.js',
  '/static/js/voice.js',
  '/static/js/lib/chart.min.js',
  '/static/manifest.json',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png'
];

// 1. Install event: Cache core static assets & offline fallback page
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      console.log('[SW] Pre-caching offline assets...');
      for (const asset of STATIC_ASSETS) {
        try {
          await cache.add(asset);
        } catch (err) {
          console.warn(`[SW] Failed to cache: ${asset}`, err);
        }
      }
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate event: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch event: Stale-while-revalidate for assets, Network-first for pages with offline fallback
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Ignore non-GET requests
  if (req.method !== 'GET') return;

  // For HTML page navigation requests
  if (req.mode === 'navigate' || req.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((networkResponse) => {
          // Clone & save visited HTML page to cache dynamically
          if (networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          }
          return networkResponse;
        })
        .catch(async () => {
          // If offline, attempt to serve cached page or fallback to /offline portal
          const cachedResponse = await caches.match(req);
          if (cachedResponse) return cachedResponse;
          return (await caches.match('/offline')) || (await caches.match('/'));
        })
    );
    return;
  }

  // For static assets (CSS, JS, Images, Fonts)
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req).then((networkResponse) => {
        if (networkResponse.status === 200) {
          const copy = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        }
        return networkResponse;
      }).catch(() => cached);

      return cached || fetchPromise;
    })
  );
});
