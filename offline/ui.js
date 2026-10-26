'use strict';
const $ = id => document.getElementById(id);
const size = bytes => (bytes / 1000000).toFixed(1) + ' MB';
let worker, catalog = [];
function selected() { return [...document.querySelectorAll('[data-pack]:checked')].map(e => e.dataset.pack); }
function total() { const ids = new Set(selected()); $('size').textContent = 'Tamanho completo da seleção: ' + size(catalog.filter(p => ids.has(p.id) || ($('all').checked && p.kind === 'source')).reduce((n, p) => n + p.downloadBytes, 0)) + '. Arquivos já salvos não são baixados novamente.'; }
function requestStatus() { worker?.postMessage({type: 'status'}); }
function appendRemove(row, id, title) {
  const remove = document.createElement('button'); remove.textContent = 'Remover download';
  remove.onclick = () => { if (confirm('Remover ' + title + '?')) worker.postMessage({type: 'remove', id}); }; row.append(remove);
}
navigator.serviceWorker?.addEventListener('message', async event => {
  const m = event.data;
  if (m.type === 'status') {
    catalog = m.packs; $('packs').replaceChildren(); $('all').checked = !!m.state.allSources;
    const stored = new Map(Object.entries(m.state.installed).filter(([id]) => id !== 'core').map(([id, pack]) => [id, pack.title]));
    for (const path of Object.keys(m.state.saved)) {
      const book = path.match(/^docs\/primary_sources\/([^/]+)\//)?.[1];
      if (book && !stored.has('source-' + book)) stored.set('source-' + book, book);
    }
    for (const p of catalog) {
      const row = document.createElement('div'), label = document.createElement('label'), input = document.createElement('input');
      input.type = 'checkbox'; input.dataset.pack = p.id;
      input.checked = p.id === 'core' || m.state.selected.includes(p.id); input.disabled = p.id === 'core';
      input.addEventListener('change', total); label.append(input, ' ' + p.title + ' — ' + size(p.downloadBytes)); row.append(label);
      if (stored.has(p.id)) { appendRemove(row, p.id, p.title); stored.delete(p.id); }
      $('packs').append(row);
    }
    for (const [id, title] of stored) {
      const row = document.createElement('div'); row.append(title); appendRemove(row, id, title); $('packs').append(row);
    }
    $('download').disabled = !catalog.length; total();
    $('status').textContent = m.state.installed.core ? 'Dicionários disponíveis sem internet.' : 'Selecione o que deseja guardar.';
    const estimate = await navigator.storage?.estimate?.();
    if (estimate) $('storage').textContent = 'Armazenamento do site: ' + size(estimate.usage || 0) + ' de até ' + size(estimate.quota || 0) + '.';
  } else if (m.type === 'progress') {
    $('status').textContent = m.text + ': ' + size(m.done) + ' / ' + size(m.total);
    $('progress').value = m.total ? m.done / m.total : 0;
  } else if (m.type === 'error' || m.type === 'complete') {
    $('status').textContent = m.text; $('download').disabled = false;
    if (m.type === 'complete') setTimeout(requestStatus, 1200);
  }
});
$('all').onchange = total;
$('pause').onclick = () => { worker?.postMessage({type: 'pause'}); $('status').textContent = 'Download pausado. Os arquivos concluídos foram mantidos.'; $('download').disabled = false; };
$('download').onclick = async () => {
  await navigator.storage?.persist?.();
  $('download').disabled = true;
  worker.postMessage({type: 'sync', selected: selected(), allSources: $('all').checked});
};
(async () => {
  try {
    await navigator.serviceWorker.register('/nhe-enga/sw.js', {scope: '/nhe-enga/'});
    worker = (await navigator.serviceWorker.ready).active; requestStatus();
  } catch (_) { $('status').textContent = 'Use HTTPS ou localhost e um navegador com suporte a armazenamento offline.'; }
  try {
    const r = await fetch('../downloads/android.json', {cache: 'no-cache'});
    if (!r.ok) return; const release = await r.json();
    $('apk').hidden = false; $('apk-size').textContent = size(release.bytes) + ' · SHA-256: ' + release.sha256;
  } catch (_) { /* No released APK yet is not an application failure. */ }
})();
