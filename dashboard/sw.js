// Offline support for the installed app. The page and the model list come from
// the network when it's there (so new models show up), falling back to the
// cache; libraries and model files rarely change, so they come from the cache
// first. Anything opened once is then viewable offline.
const CACHE = 'models-v1';
const SHELL = ['./', 'index.html', 'models.json', 'manifest.webmanifest', 'icon.svg'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const networkFirst = async req => {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req, { cache: 'no-store' });
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch {
    return (await cache.match(req, { ignoreSearch: true })) || Response.error();
  }
};

const cacheFirst = async req => {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
};

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === location.origin;
  const isShell = sameOrigin && (req.mode === 'navigate' || /\/(index\.html|models\.json)?$/.test(url.pathname));
  if (isShell) e.respondWith(networkFirst(req));
  else if (sameOrigin || url.hostname === 'cdn.jsdelivr.net') e.respondWith(cacheFirst(req));
});
