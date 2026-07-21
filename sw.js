const CACHE_NAME = 'rutas-lenas-v2'; // <-- Versión 2 para limpiar el caché viejo

self.addEventListener('install', (e) => {
  self.skipWaiting(); // Obliga a instalar la nueva versión al instante
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        './',
        './index.html'
      ]);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => {
      return caches.match(e.request);
    })
  );
});
