/* Small shared hook; no service-worker layer inside the native local origin. */
(() => {
  if (location.hostname === 'appassets.androidplatform.net') return;
  const base = '/nhe-enga/';
  function link() {
    if (!document.body || document.getElementById('offline-link')) return;
    const install = document.getElementById('android-install');
    const android = navigator.userAgentData?.platform === 'Android' || /Android/i.test(navigator.userAgent);
    if (install && android) {
      fetch(base + 'downloads/android.json', {cache: 'no-store'}).then(async response => {
        if (!response.ok) return;
        const release = await response.json();
        if (release.url !== 'nhe-enga.apk' || !Number.isSafeInteger(release.versionCode) || release.versionCode < 1 ||
            !Number.isSafeInteger(release.bytes) || release.bytes <= 0 || release.bytes > 15 * 1024 * 1024 ||
            typeof release.versionName !== 'string' || !/^[a-f0-9]{64}$/.test(release.sha256)) return;
        document.getElementById('android-install-version').textContent = 'Versão ' + release.versionName + ' · ' + (release.bytes / 1000000).toFixed(1) + ' MB';
        install.onclick = () => document.getElementById('android-install-dialog').showModal();
        install.hidden = false;
      }).catch(() => {});
      return;
    }
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
