// public/beef-sw.js
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('zalo-pay-v1').then(function(cache) {
            return cache.addAll([
                '/beef-persistence.js',
                '/hook-reload.js'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    // You can add fetch handling logic here if needed
});