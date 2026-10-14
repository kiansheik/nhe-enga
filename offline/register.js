/* Small shared hook; no service-worker layer inside the native local origin. */
(() => {
  if (location.hostname === 'appassets.androidplatform.net') return;
  const base = '/nhe-enga/';
  function link() {
    if (!document.body || document.getElementById('offline-link')) return;
    const a = document.createElement('a');
    a.id = 'offline-link'; a.href = base + 'offline/'; a.textContent = 'Usar sem internet · Android';
    a.style.cssText = 'display:block;text-align:center;margin:1rem;font:14px system-ui';
    document.body.appendChild(a);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', link); else link();
  if ('serviceWorker' in navigator) {
    const check = () => navigator.serviceWorker.ready.then(r => r.active?.postMessage({type: 'check'}));
    navigator.serviceWorker.register(base + 'sw.js', {scope: base}).then(check).catch(console.warn);
    addEventListener('online', check);
  }
})();
