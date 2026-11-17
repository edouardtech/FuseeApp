// Garde le jeu dans le téléphone pour pouvoir jouer sans wifi.
// Change VERSION à chaque nouvelle version du jeu pour que tout le monde la reçoive.
const VERSION = 'fusee-karman-2026-11-17';
const FILES = ['./', './index.html', './three.min.js', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  // D'abord ce qui est gardé dans le téléphone ; sinon internet, et on le garde pour la prochaine fois (polices d'écriture…)
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(res => {
    if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
    return res;
  }).catch(() => caches.match('./index.html'))));
});
