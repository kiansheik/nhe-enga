/* Protocol-level SW tests with standard Node Web APIs; real-browser test is separate. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
const root = path.resolve(__dirname, '../..'), tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'nhe-sw-')), site = path.join(tmp, 'nhe-enga');
const origin = 'https://fixture.invalid';
let offline = false;
const requests = [], events = [], stores = new Map();
const abs = value => new URL(typeof value === 'string' ? value : value.url, origin).href;
const caches = {async open(name) {
  if (!stores.has(name)) stores.set(name, new Map()); const m = stores.get(name);
  return {async match(k) {return m.get(abs(k))?.clone();}, async put(k, v) {m.set(abs(k), v.clone());}, async delete(k) {return m.delete(abs(k));}, async keys() {return [...m.keys()].map(url => new Request(url));}};
}};
const sandbox = {URL, Request, Response, Headers, TextDecoder, Uint8Array, Set, Map, Date, console, crypto: webcrypto, atob, caches,
  fetch: async url => {
    if (offline) throw Error('Network offline');
    const u = new URL(typeof url === 'string' ? url : url.url, origin); requests.push(u.pathname);
    try {return new Response(fs.readFileSync(path.join(tmp, decodeURIComponent(u.pathname))));} catch (_) {return new Response('', {status:404});}
  },
  self: {location: {origin}, clients: {async matchAll(){return [{id:'test', postMessage: m => events.push(m)}];}, async claim(){}}, addEventListener(){}, skipWaiting(){}},
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'offline/sw.js'), 'utf8'), sandbox);
async function call(code) {return await vm.runInContext(code, sandbox);}
async function serve(client, url, navigate = false) {
  const waits = [];
  const request = new Request(origin + '/nhe-enga/' + url);
  if (navigate) Object.defineProperty(request, 'mode', {value: 'navigate'});
  sandbox.event = {request, clientId: client, resultingClientId: client, waitUntil: p => waits.push(p)};
  const result = await call('serve(event)'); await Promise.all(waits); return result;
}
try {
  cp.execFileSync('python3', [path.join(root,'tests/offline/fixture.py'), site]);
  (async () => {
    await call('sync()');
    offline = true;
    assert.match(await (await serve('old', '')).text(), />v1</);
    assert.equal((await serve('old', 'js/index.js')).status, 200);
    console.log('PASS core offline fetch and canonical directory navigation');
    offline = false;
    await call("sync({selected:['core','source-vlb']})");
    assert(!requests.some(p => p.endsWith('/lerhist/2.png')));
    offline = true;
    assert.equal((await serve('citation', 'docs/primary_sources/?book_name=vlb&page_number=1')).status, 200);
    assert.equal((await serve('citation', 'docs/primary_sources/vlb/1.png')).status, 200);
    console.log('PASS selective source packs and query-independent static document caching');
    offline = false;
    let text = fs.readFileSync(path.join(site,'index.html'),'utf8');
    fs.writeFileSync(path.join(site,'index.html'), text.replace('>v1<','>v2<'));
    cp.execFileSync('python3',[path.join(root,'scripts/build_offline.py'),site], {env:{...process.env,OFFLINE_SEQUENCE:'2'}});
    assert.match(await (await serve('fresh-navigation','',true)).text(), />v2</);
    offline = true;
    assert.match(await (await serve('old','')).text(), />v1</);
    console.log('PASS navigation revalidates the catalog while existing documents stay pinned');
    offline = false;
    const before = requests.filter(p => p.endsWith('/vlb/1.png')).length;
    await call('sync()');
    assert.equal(requests.filter(p => p.endsWith('/vlb/1.png')).length,before);
    offline = true;
    assert.match(await (await serve('old','')).text(), />v1</);
    assert.match(await (await serve('new','')).text(), />v2</);
    console.log('PASS per-document snapshot, next-navigation activation, unchanged-file deduplication');
    offline = false;
    fs.writeFileSync(path.join(site,'index.html'), text.replace('>v1<','>v3<'));
    cp.execFileSync('python3',[path.join(root,'scripts/build_offline.py'),site], {env:{...process.env,OFFLINE_SEQUENCE:'3'}});
    fs.writeFileSync(path.join(site,'index.html'), 'corrupt');
    await assert.rejects(call('sync()'), /corrompido/);
    offline = true;
    assert.match(await (await serve('after-error','')).text(), />v2</);
    console.log('PASS corrupt update does not replace the active offline library');
  })().catch(error => {console.error(error); process.exitCode = 1;}).finally(() => fs.rmSync(tmp,{recursive:true,force:true}));
} catch(error) {fs.rmSync(tmp,{recursive:true,force:true}); throw error;}
