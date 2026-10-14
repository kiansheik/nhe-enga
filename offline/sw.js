/* Browser adapter. Android uses native durable storage instead of this cache. */
'use strict';
const BASE = '/nhe-enga/';
const META = 'nhe-offline-meta-v1';
const BLOBS = 'nhe-offline-blobs-v1';
const STATE = new URL(BASE + 'offline/state', self.location.origin).href;
let queue = Promise.resolve();
let cancelled = false;
const empty = () => ({installed: {}, selected: ['core'], saved: {}, allSources: false, paused: false});
const key = hash => new URL(BASE + 'offline/blob/' + hash, self.location.origin).href;
const sha = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
const pathOK = p => typeof p === 'string' && p.length > 0 && !p.startsWith('/') && !/[\\%?#\x00]/.test(p) && !p.split('/').some(s => !s || s === '.' || s === '..');
async function state() { const r = await (await caches.open(META)).match(STATE); return r ? r.json() : empty(); }
async function write(value) { await (await caches.open(META)).put(STATE, new Response(JSON.stringify(value))); }
async function notify(value) { for (const c of await self.clients.matchAll()) c.postMessage(value); }
function assetURL(path) { if (!pathOK(path)) throw Error('Caminho inválido'); return BASE + path.split('/').map(encodeURIComponent).join('/'); }
function decodeCatalog(envelope) {
  const raw = Uint8Array.from(atob(envelope.payload), c => c.charCodeAt(0));
  const value = JSON.parse(new TextDecoder().decode(raw));
  if (value.schema !== 1 || value.minShell > 1 || value.base !== BASE || !Number.isSafeInteger(value.sequence)) throw Error('Catálogo incompatível');
  if (!Array.isArray(value.packs) || !value.packs.some(p => p.id === 'core')) throw Error('Catálogo sem dicionários');
  const seen = new Set();
  for (const p of value.packs) {
    if (seen.has(p.id) || !/^[a-z0-9_-]+$/.test(p.id) || !pathOK(p.url) || !/^[a-f0-9]{64}$/.test(p.sha256)) throw Error('Pacote inválido');
    seen.add(p.id);
  }
  return value;
}
async function catalog(refresh = false) {
  const cache = await caches.open(META), url = BASE + 'offline/catalog.json';
  const old = await cache.match(url);
  if (old && !refresh) return decodeCatalog(await old.json());
  const headers = {};
  if (old?.headers.get('ETag')) headers['If-None-Match'] = old.headers.get('ETag');
  const r = await fetch(url, {cache: 'no-cache', headers});
  if (r.status === 304 && old) return decodeCatalog(await old.json());
  if (!r.ok) throw Error('Não foi possível consultar as atualizações');
  const bytes = await r.arrayBuffer();
  if (bytes.byteLength > 1024 * 1024) throw Error('Catálogo muito grande');
  const value = decodeCatalog(JSON.parse(new TextDecoder().decode(bytes)));
  if (old && value.sequence < decodeCatalog(await old.clone().json()).sequence) throw Error('Catálogo antigo recusado');
  await cache.put(url, new Response(bytes, {headers: r.headers}));
  return value;
}
async function manifest(pack) {
  const cache = await caches.open(META), url = assetURL(pack.url);
  const cached = await cache.match(url);
  const response = cached || await fetch(url, {cache: 'no-cache'});
  if (!response.ok) throw Error('Manifesto indisponível: ' + pack.title);
  const bytes = await response.arrayBuffer();
  if (bytes.byteLength !== pack.bytes || await sha(bytes) !== pack.sha256) throw Error('Manifesto corrompido');
  const value = JSON.parse(new TextDecoder().decode(bytes)), seen = new Set();
  if (value.id !== pack.id || !Array.isArray(value.files)) throw Error('Manifesto inválido');
  for (const f of value.files) {
    if (!pathOK(f.path) || seen.has(f.path) || !/^[a-f0-9]{64}$/.test(f.sha256) || !Number.isSafeInteger(f.bytes) || f.bytes < 0) throw Error('Arquivo inválido');
    seen.add(f.path);
  }
  if (!cached) await cache.put(url, new Response(bytes));
  return value;
}
async function getBlob(file, bulk = false) {
  const cache = await caches.open(BLOBS), url = key(file.sha256);
  let response = await cache.match(url);
  if (response) return response;
  if (bulk && cancelled) throw Error('Download pausado');
  response = await fetch(assetURL(file.path), {cache: 'no-cache'});
  if (!response.ok) throw Error('Arquivo indisponível: ' + file.path);
  const bytes = await response.arrayBuffer();
  if (bulk && cancelled) throw Error('Download pausado');
  if (bytes.byteLength !== file.bytes || await sha(bytes) !== file.sha256) throw Error('Arquivo corrompido: ' + file.path);
  const verified = new Response(bytes, {headers: {'Content-Type': file.mime, 'X-Nhe-Offline': 'verified'}});
  await cache.put(url, verified.clone());
  return verified;
}
async function sync(options = {}) {
  cancelled = false;
  let s = await state(); s.paused = false;
  if (options.selected) s.selected = [...new Set(['core', ...options.selected])];
  if (typeof options.allSources === 'boolean') s.allSources = options.allSources;
  await write(s);
  const c = await catalog(true), selected = new Set(s.selected);
  if (s.allSources) c.packs.filter(p => p.kind === 'source').forEach(p => selected.add(p.id));
  // Missing/retired packs are retained, never silently deleted.
  const next = {...s.installed};
  const work = c.packs.filter(p => selected.has(p.id)).sort((a, b) => (a.id === 'core' ? -1 : b.id === 'core' ? 1 : a.id.localeCompare(b.id)));
  for (const p of work) {
    if (s.installed[p.id]?.hash === p.sha256) continue;
    const m = await manifest(p);
    let done = 0;
    for (const f of m.files) {
      await getBlob(f, true); done += f.bytes;
      await notify({type: 'progress', text: p.title, done, total: p.downloadBytes});
    }
    next[p.id] = {hash: p.sha256, files: m.files, title: p.title};
    // First-time dictionary use need not wait for a 600 MB image download.
    if (p.id === 'core' && !s.installed.core) {
      s = await state(); s.installed.core = next.core; await write(s);
    }
  }
  if (cancelled) throw Error('Download pausado');
  // Previously viewed files also subscribe to updates without an entire book.
  const saved = {...(await state()).saved};
  if (Object.keys(saved).length) {
    for (const p of c.packs.filter(p => p.kind !== 'source' || Object.keys(saved).some(path => path.startsWith('docs/primary_sources/' + p.id.slice(7) + '/')))) {
      const m = await manifest(p);
      for (const f of m.files) if (saved[f.path] && saved[f.path].sha256 !== f.sha256) {
        await getBlob(f, true); saved[f.path] = f;
      }
    }
  }
  s = await state(); s.installed = next; s.saved = {...s.saved, ...saved}; s.lastCheck = Date.now();
  await write(s);
  await notify({type: 'complete', text: 'Downloads concluídos. Reabra a página para usar a versão nova.'});
}
async function pin(clientId, s) {
  if (!clientId) return s;
  const cache = await caches.open(META), url = BASE + 'offline/client/' + encodeURIComponent(clientId);
  const old = await cache.match(url);
  if (old) return old.json();
  const snapshot = {installed: s.installed, saved: s.saved, catalog: await catalog().catch(() => null)};
  await cache.put(url, new Response(JSON.stringify(snapshot)));
  return snapshot;
}
async function findFile(path, snapshot) {
  for (const p of Object.values(snapshot.installed)) {
    const f = p.files.find(f => f.path === path); if (f) return f;
  }
  if (snapshot.saved[path]) return snapshot.saved[path];
  const c = snapshot.catalog || await catalog();
  // Source packs use the real directory name; all other pages are core/tools.
  const book = path.match(/^docs\/primary_sources\/([^/]+)\//)?.[1];
  const packs = book ? c.packs.filter(p => p.id === 'source-' + book || p.id === 'core') : c.packs.filter(p => p.kind !== 'source');
  for (const p of packs) { const f = (await manifest(p)).files.find(f => f.path === path); if (f) return f; }
  return null;
}
async function serve(event) {
  const url = new URL(event.request.url);
  let path = decodeURIComponent(url.pathname.slice(BASE.length));
  if (!path || path.endsWith('/')) path += 'index.html';
  else if (!path.split('/').pop().includes('.')) path += '/index.html';
  if (!pathOK(path)) return new Response('Caminho inválido', {status: 400});
  const s = await state(), snapshot = await pin(event.resultingClientId || event.clientId, s);
  try {
    const f = await findFile(path, snapshot);
    if (f) {
      const response = await getBlob(f);
      // Serialise state writes with sync, but do not hold the fetch response up.
      event.waitUntil(queue = queue.catch(() => {}).then(async () => {
        const latest = await state(); if (!latest.saved[path]) latest.saved[path] = f; await write(latest);
      }));
      return response;
    }
    return await fetch(event.request);
  } catch (_) {
    if (event.request.mode === 'navigate') return new Response('<!doctype html><meta charset="utf-8"><p>Esta página ainda não foi baixada.</p><a href="' + BASE + 'offline/">Gerenciar downloads</a>', {status: 503, headers: {'Content-Type': 'text/html; charset=utf-8'}});
    return new Response('Este arquivo ainda não foi baixado.', {status: 503});
  }
}
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  const u = new URL(event.request.url);
  if (event.request.method !== 'GET' || u.origin !== self.location.origin || !u.pathname.startsWith(BASE)) return;
  if (u.pathname.startsWith(BASE + 'downloads/') || u.pathname === BASE + 'sw.js' || u.pathname.startsWith(BASE + 'offline/catalog') || u.pathname.startsWith(BASE + 'offline/packs/')) return;
  event.respondWith(serve(event));
});
self.addEventListener('message', event => {
  const msg = event.data || {};
  if (msg.type === 'pause') { cancelled = true; event.waitUntil(queue = queue.catch(() => {}).then(async () => {const s = await state(); s.paused = true; await write(s);})); return; }
  event.waitUntil(queue = queue.catch(() => {}).then(async () => {
    try {
      if (msg.type === 'sync' || msg.type === 'check') {
        const s = await state();
        if (msg.type !== 'check' || (!s.paused && (!s.lastCheck || Date.now() - s.lastCheck > 6 * 3600000))) await sync(msg);
      } else if (msg.type === 'status') {
        const s = await state(); let c;
        try { c = await catalog(); } catch (_) { c = {packs: []}; }
        event.source?.postMessage({type: 'status', state: s, packs: c.packs});
      } else if (msg.type === 'remove' && msg.id !== 'core') {
        const s = await state();
        const removed = s.installed[msg.id];
        delete s.installed[msg.id]; s.selected = s.selected.filter(id => id !== msg.id); s.allSources = false;
        for (const f of removed?.files || []) delete s.saved[f.path];
        await write(s);
        // GC is explicit, never storage-pressure eviction of user downloads.
        // Existing documents retain their pinned versions until closed.
        const keep = new Set(Object.values(s.installed).flatMap(p => p.files).concat(Object.values(s.saved)).map(f => f.sha256));
        const meta = await caches.open(META);
        const live = new Set((await self.clients.matchAll()).map(c => c.id));
        for (const req of await meta.keys()) if (req.url.includes('/offline/client/')) {
          if (!live.has(decodeURIComponent(req.url.split('/').pop()))) { await meta.delete(req); continue; }
          const pinned = await (await meta.match(req)).json();
          for (const p of Object.values(pinned.installed)) for (const f of p.files) keep.add(f.sha256);
          for (const f of Object.values(pinned.saved)) keep.add(f.sha256);
        }
        const blobs = await caches.open(BLOBS);
        for (const req of await blobs.keys()) if (!keep.has(req.url.split('/').pop())) await blobs.delete(req);
        event.source?.postMessage({type: 'complete', text: 'Pacote removido. Feche as páginas abertas para liberar cópias em uso.'});
      }
    } catch (error) { event.source?.postMessage({type: 'error', text: error.message}); }
  }));
});
