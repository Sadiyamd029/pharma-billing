self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
self.addEventListener('fetch', (e) => {
    // Pass-through only — always hits your live server, never caches billing/stock data
    e.respondWith(fetch(e.request));
});