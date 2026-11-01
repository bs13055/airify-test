// Run after the github-pages build. Leave ordinary Vite/local builds untouched.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const dist = path.resolve(__dirname, '../dist');
const entry = path.join(dist, 'index.html');
assert.ok(fs.existsSync(path.join(dist, 'gp1/index.html')), 'Build GP1 pages first');
const previous = fs.readFileSync(entry, 'utf8');
if (!previous.includes('airify-gp1-entry')) {
  assert.ok(previous.includes('/Airify/assets/'), 'Run the github-pages build first');
  fs.writeFileSync(path.join(dist, 'platform.html'), previous);
}
const redirect = `<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="airify-gp1-entry" content="20261101">
<title>Airify — Air Quality. Made Personal.</title>
<meta http-equiv="refresh" content="0;url=./gp1/">
<link rel="canonical" href="https://bs13055.github.io/Airify/gp1/">
<script>location.replace(new URL('./gp1/', location.href).href);</script>
</head><body><p><a href="./gp1/">เปิดเว็บไซต์ Airify</a></p></body></html>
`;
fs.writeFileSync(entry, redirect);
// Retire the old cache-first worker at its existing URL so returning visitors
// also reach the new entry point. Browser profile/history storage is untouched.
const worker = `'use strict';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key === 'airify-v1-static').map(key => caches.delete(key)));
    await self.clients.claim();
    const scope = new URL(self.registration.scope);
    const windows = await self.clients.matchAll({type:'window'});
    await Promise.all(windows.map(client => {
      const url = new URL(client.url);
      if (url.origin === scope.origin && (url.pathname === scope.pathname || url.pathname === scope.pathname + 'index.html')) {
        return client.navigate(new URL('gp1/', scope).href);
      }
    }));
  })());
});
// No fetch handler: navigations and API requests use the network normally.
`;
fs.writeFileSync(path.join(dist, 'service-worker.js'), worker);
console.log('Pages entry now opens GP1; previous React entry preserved at platform.html.');
