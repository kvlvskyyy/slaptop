const CACHE_NAME = 'stickerdom-v1';
const ASSETS_TO_CACHE = [
    '/offline',                 // The offline page route
    '/static/styles.css',       // Your main CSS
    '/static/images/icons/Logo.svg',
    '/static/images/bg/bg.jpg',
    '/static/images/icons/icon-192.png',
    '/static/images/icons/icon-512.png',
    '/static/images/icons/Logo_squared.png',
    '/static/images/icons/Logo.png',
    
    // External Libraries (Bootstrap, Icons, AOS)
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
    'https://unpkg.com/aos@2.3.1/dist/aos.css',
    'https://unpkg.com/aos@2.3.1/dist/aos.js'
];

// 1. INSTALL: Cache resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching all: app shell and content');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. ACTIVATE: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// 3. FETCH: Intercept requests
self.addEventListener('fetch', (event) => {
    // A. For HTML pages (Navigation): Network First, fall back to Offline Page
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match('/offline');
            })
        );
        return;
    }

    // B. For CSS/Images/JS: Cache First, fall back to Network
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || fetch(event.request);
        })
    );
});