const CACHE_NAME = 'medilensai-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/reports',
  '/alerts',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/charts.js',
  '/static/js/voice.js',
  '/static/js/lib/chart.min.js',
  '/static/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  // Network first, falling back to cache
  e.respondWith(
    fetch(e.request).catch(() => {
      return caches.match(e.request);
    })
  );
});
