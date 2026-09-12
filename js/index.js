(() => {
  'use strict';

  const DATA_PATH = 'docs/dict-conjugated.json.gz';
  const NEO_PATH = '/nhe-enga/neologisms.csv';

  const MODES = ['indicativo', 'permissivo', 'circunstancial', 'gerundio', 'imperativo', 'conjuntivo'];
  const TUPI_START_RE = /^[A-Za-zÀ-ÿ\u0176\u0177'’]/;
  const TUPI_DIALOGUE_RE = /^-[A-Za-zÀ-ÿ\u0176\u0177'’]/;
  const TUPI_DIALOGUE_LEAD_RE = /^-[A-Za-zÀ-ÿ\u0176\u0177'’]?\s*/;
  const TUPI_LETTER_RE = /[A-Za-zÀ-ÿ\u0176\u0177'’]/;
  const TUPI_HEAD_CHAR_RE = /[A-Za-zÀ-ÿ\u0176\u0177'’\\-]/;

  const SUBJ_PREF_MAP = {
    'ø': null,
    'ixé': '1ps',
    'endé': '2ps',
    "a'e": '3p',
    'oré': '1ppe',
    'îandé': '1ppi',
    'peẽ': '2pp',
  };

  const OBJ_PREF_MAP = {
    'ø': null,
    'xe': '1ps',
    'nde': '2ps',
    'i': '3p',
    'oré': '1ppe',
    'îandé': '1ppi',
    'pe': '2pp',
    'îe': 'refl',
    'îo': 'mut',
  };

  const PERSON_META = {
    '1ps': {
      rank: 1,
      rankSymbol: '1',
      term: '1ª pessoa singular',
      ptSubj: 'eu',
      ptObj: 'me',
    },
    '2ps': {
      rank: 2,
      rankSymbol: '2',
      term: '2ª pessoa singular',
      ptSubj: 'você',
      ptObj: 'te',
    },
    '3p': {
      rank: 3,
      rankSymbol: '3',
      term: '3ª pessoa (sg/pl; sem gênero)',
      ptSubj: 'el@',
      ptObj: '@s',
    },
    '1ppe': {
      rank: 1,
      rankSymbol: '1',
      term: '1ª pessoa plural (excl.)',
      ptSubj: 'nós (excl.)',
      ptObj: 'nos (excl.)',
    },
    '1ppi': {
      rank: 1,
      rankSymbol: '1',
      term: '1ª pessoa plural (incl.)',
      ptSubj: 'nós (incl.)',
      ptObj: 'nos (incl.)',
    },
    '2pp': {
      rank: 2,
      rankSymbol: '2',
      term: '2ª pessoa plural',
      ptSubj: 'vocês',
      ptObj: 'vos',
    },
    'refl': {
      rank: 0,
      rankSymbol: '=',
      term: 'reflexivo',
      ptSubj: 'se',
      ptObj: 'se',
    },
    'mut': {
      rank: 0,
      rankSymbol: '↔',
      term: 'mútuo',
      ptSubj: 'um ao outro',
      ptObj: 'um ao outro',
    },
  };

  const PERSON_RANK = {
    '1ps': 1,
    '1ppe': 1,
    '1ppi': 1,
    '2ps': 2,
    '2pp': 2,
    '3p': 3,
  };

  const PERSON_ORDER = {
    '1ps': 1,
    '1ppe': 2,
    '1ppi': 3,
    '2ps': 4,
    '2pp': 5,
    '3p': 6,
    'refl': 7,
    'mut': 8,
    null: 9,
    undefined: 9,
  };

  const searchButton = document.getElementById('searchButton');
  const searchInput = document.getElementById('searchInput');
  const resultsDiv = document.getElementById('results');
  const toggleContainer = document.getElementById('toggleContainer');
  const toggleBall = document.getElementById('toggleBall');

  let jsonData = [];
  let searchIndex = [];
  let dataReady = false;

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function removePunctuation(str) {
    return str.replace(/[.,\/#!$%?^&*;:{}=\-_`~()]/g, '').trim();
  }

  function removeDiacritics(str) {
    return removePunctuation(str.normalize('NFD').replace(/[\u0300-\u036f]/g, ''));
  }

  function stripDiacritics(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function normalizeExact(str) {
    return removePunctuation(str).toLowerCase();
  }

  function normalizeNoAccent(str) {
    return removeDiacritics(str).toLowerCase();
  }

  function buildSearchIndex(data) {
    return data.map((item) => ({
      item,
      firstWordExact: normalizeExact(item.first_word || ''),
      firstWordNoAccent: normalizeNoAccent(item.first_word || ''),
      definitionLower: (item.definition || '').toLowerCase(),
      definitionNoAccent: normalizeNoAccent(item.definition || ''),
    }));
  }

  const warnOnce = (() => {
    const seen = new Set();
    return (label, text) => {
      const key = `${label}::${text}`;
      if (seen.has(key)) return;
      seen.add(key);
      console.warn(label, text);
    };
  })();

  async function fetchCompressedJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    const buffer = await response.arrayBuffer();
    const decompressedData = pako.inflate(new Uint8Array(buffer), { to: 'string' });
    return JSON.parse(decompressedData);
  }

  function buildNeoJSON(rows) {
    const jsonDataList = [];

    rows.forEach((row) => {
      const firstWord = row['Verbete'] || '';
      let pluriforme = row['Pluriforme'] || '';
      if (pluriforme === 'Nenhuma') {
        pluriforme = '';
      }

      const categoria = (row['Categoria Gramatical'] || '').toLowerCase();
      let transitividade = row['Transitividade'] || '';

      if (transitividade === 'intr.-estativo (adjetivos, substantivos)') {
        if (categoria.includes('subs') || categoria.includes('noun')) {
          transitividade = '(s.)';
        } else if (categoria.includes('adv')) {
          transitividade = '(adv.)';
        } else {
          transitividade = '(xe) (v. da 2ª classe)';
        }
      } else if (transitividade === 'tr.-activo') {
        transitividade = '(v.tr.)';
      } else if (transitividade === 'intr.-activo') {
        transitividade = '(v. intr.)';
      } else {
        transitividade = '';
      }

      let verbeteBase = row['Verbete(s) Base(s)'] || '';
      if (verbeteBase) {
        verbeteBase = `(etim. - ${verbeteBase})`;
      }

      const traducaoPt = row['Tradução Portuguesa'] ? `- ${row['Tradução Portuguesa']}` : '';
      const traducaoEn = row['Tradução Inglesa'] ? `- ${row['Tradução Inglesa']}` : '';
      const englishDefinition = row['English Definition'] ? `| ${row['English Definition']}` : '';

      const definitionRaw = `${pluriforme} ${transitividade} ${verbeteBase} - ${row['Definição Portuguesa'] || ''} ${englishDefinition} | ${row['Atestação'] || ''} ${traducaoPt} ${traducaoEn} (${row['Fonte'] || ''}, ${row['Data da Fonte'] || ''}, ${row['Pagina(s) na Fonte'] || ''}) - neologismo`;
      const definition = definitionRaw.replace(/\s{2,}/g, ' ').trim();

      jsonDataList.push({
        first_word: firstWord,
        optional_number: '',
        con: '',
        definition,
        type: 'neo',
      });
    });

    return jsonDataList;
  }

  async function fetchNeoCSV(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    const csvText = await response.text();
    const results = Papa.parse(csvText, {
      skipEmptyLines: true,
      header: true,
      dynamicTyping: false,
    });
    return buildNeoJSON(results.data);
  }

  function mapCompressedData(data) {
    return data.map((item, index) => ({
      first_word: item.f || '',
      optional_number: item.o || '',
      definition: item.d || '',
      con: item.c || '',
      is_tupi_portuguese: item.t === 1 || item.t === true,
    }));
  }

  function keyForItem(item) {
    return `${item.first_word}||${item.definition}`;
  }

  function searchByFirstWord(entries, query) {
    const queryNorm = normalizeExact(query);
    return entries.filter((entry) => entry.firstWordExact === queryNorm);
  }

  function searchInFirstWord(entries, query) {
    const queryNorm = normalizeExact(query);
    return entries.filter((entry) => entry.firstWordExact.includes(queryNorm));
  }

  function searchAllDefinitions(entries, queryLower) {
    const escapedQuery = escapeRegExp(queryLower);
    const regex = new RegExp(`(^|[\\s.,;:!?()\"])${escapedQuery}($|[\\s.,;:!?()\"])`, 'i');
    const filtered = entries.filter(
      (entry) => entry.item.first_word.toLowerCase() !== queryLower && regex.test(entry.definitionLower)
    );
    filtered.sort(
      (a, b) => a.definitionLower.indexOf(queryLower) - b.definitionLower.indexOf(queryLower)
    );
    return filtered;
  }

  function searchByFirstWordNoAccent(entries, query) {
    const queryNorm = normalizeNoAccent(query);
    return entries.filter((entry) => entry.firstWordNoAccent === queryNorm);
  }

  function searchAllDefinitionsNoAccent(entries, query) {
    const queryNorm = normalizeNoAccent(query);
    const escapedQuery = escapeRegExp(queryNorm);
    const regex = new RegExp(`(^|[\\s.,;:!?()\"])${escapedQuery}($|[\\s.,;:!?()\"])`, 'i');
    const filtered = entries.filter(
      (entry) => entry.firstWordNoAccent !== queryNorm && regex.test(entry.definitionNoAccent)
    );
    filtered.sort(
      (a, b) => a.definitionNoAccent.indexOf(queryNorm) - b.definitionNoAccent.indexOf(queryNorm)
    );
    return filtered;
  }

  function searchAllDefinitionsNoBounds(entries, query) {
    const queryNorm = normalizeNoAccent(query);
    const escapedQuery = escapeRegExp(queryNorm);
    const regex = new RegExp(escapedQuery, 'i');
    const filtered = entries.filter(
      (entry) => entry.firstWordNoAccent !== queryNorm && regex.test(entry.definitionNoAccent)
    );
    filtered.sort(
      (a, b) => a.definitionNoAccent.indexOf(queryNorm) - b.definitionNoAccent.indexOf(queryNorm)
    );
    return filtered;
  }

  function transformConjList(mode, list, negar) {
    const resultObject = {};
    list.forEach((obj) => {
      if (obj.m.slice(0, 2) === mode.slice(0, 2)) {
        const key = [obj.s, obj.o];
        resultObject[JSON.stringify(key)] = negar ? obj.n : obj.f;
      }
    });

    return resultObject;
  }

  function getPersonMeta(code, role) {
    if (code === null || code === undefined) {
      return {
        rank: 0,
        rankSymbol: 'Ø',
        term: 'impessoal',
        pt: '—',
      };
    }

    const meta = PERSON_META[code] || {};
    return {
      rank: meta.rank || 0,
      rankSymbol: meta.rankSymbol || '',
      term: meta.term || '',
      pt: role === 'subj' ? meta.ptSubj || '' : meta.ptObj || '',
    };
  }

  function isIntransitive(objectsVals) {
    return objectsVals.length === 0 || (objectsVals.length === 1 && objectsVals[0] === null);
  }

  function getMorphKind(subj, obj) {
    if (obj === 'refl' || obj === 'mut') return 'equal';

    const subjRank = PERSON_RANK[subj];
    const objRank = PERSON_RANK[obj];

    if (!subjRank || !objRank) return 'neutral';
    if (subjRank === objRank) return 'equal';
    return subjRank < objRank ? 'active' : 'stative';
  }

  function getReflexivePt(subj) {
    switch (subj) {
      case '1ps':
        return 'me';
      case '2ps':
        return 'te';
      case '3p':
        return 'se';
      case '1ppe':
      case '1ppi':
        return 'nos';
      case '2pp':
        return 'vos';
      default:
        return 'se';
    }
  }

  function getBucketKey(subj, obj) {
    if (obj === 'refl' || obj === 'mut') {
      return obj === 'mut' ? 'mut' : 'refl';
    }

    const subjRank = PERSON_RANK[subj] || 0;
    const objRank = PERSON_RANK[obj] || 0;
    if (!subjRank || !objRank) return null;
    return subjRank === 3 || objRank === 3 ? '123-3' : '12';
  }

  function renderPairLine(subj, obj, conj, morphKind) {
    const subjMeta = getPersonMeta(subj, 'subj');
    const objMeta = getPersonMeta(obj, 'obj');
    const objPt = obj === 'refl' ? getReflexivePt(subj) : objMeta.pt;
    const ptLine = subjMeta.pt && objPt ? `${subjMeta.pt} ${objPt}` : '';

    return `
      <div class="conj-line morph-${morphKind || 'neutral'}">
        <span class="conj-form">${conj}</span>
        ${ptLine ? `<span class="conj-gloss">${ptLine}</span>` : ''}
      </div>
    `;
  }

  function renderSubjectLine(subj, conj) {
    const subjMeta = getPersonMeta(subj, 'subj');
    const ptLine = subjMeta.pt || '';
    return `
      <div class="conj-line morph-neutral">
        <span class="conj-form">${conj}</span>
        ${ptLine ? `<span class="conj-gloss">${ptLine}</span>` : ''}
      </div>
    `;
  }

  function renderObjectLine(obj, conj) {
    const objMeta = getPersonMeta(obj, 'obj');
    const ptLine = objMeta.pt || '';
    return `
      <div class="conj-line morph-neutral">
        <span class="conj-form">${conj}</span>
        ${ptLine ? `<span class="conj-gloss">${ptLine}</span>` : ''}
      </div>
    `;
  }

  function generateConjugationTableImperative({
    conjugations,
    subjectsVals,
    objectsVals,
    unId,
    negar,
  }) {
    const groups = {
      sing: { active: [], stative: [], refl: [] },
      pl: { active: [], stative: [], refl: [] },
    };

    const subjGroupFor = (subj) => (subj === '2pp' ? 'pl' : 'sing');

    subjectsVals.forEach((subj) => {
      objectsVals.forEach((obj) => {
        const conj = conjugations[JSON.stringify([subj, obj])] || '-';
        if (!conj || conj === '-') return;
        const groupKey = subjGroupFor(subj);

        if (obj === 'refl' || obj === 'mut') {
          groups[groupKey].refl.push(renderPairLine(subj, obj, conj, 'equal'));
          return;
        }

        const objRank = PERSON_RANK[obj];
        if (objRank === 1) {
          groups[groupKey].stative.push(renderPairLine(subj, obj, conj, 'stative'));
        } else if (objRank === 3) {
          groups[groupKey].active.push(renderPairLine(subj, obj, conj, 'active'));
        } else {
          groups[groupKey].refl.push(renderPairLine(subj, obj, conj, 'equal'));
        }
      });
    });

    const renderGroupCell = (items) => (items.length ? items.join('') : '<div class="conj-empty">—</div>');

    let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
    htmlString += renderControls(unId, negar);
    htmlString += `
      <table class="conj-rank-table conj-imperative-table">
        <colgroup>
          <col class="conj-col-rowhead">
          <col class="conj-col-main">
          <col class="conj-col-main">
          <col class="conj-col-side">
        </colgroup>
        <thead>
          <tr class="conj-subhead is-active">
            <th></th>
            <th>2 &gt; 3</th>
            <th>2 &gt; 1</th>
            <th class="conj-side-head">Reflexivo / Mútuo</th>
          </tr>
        </thead>
        <tbody>
          <tr class="conj-group">
            <th class="conj-rowhead">Singular</th>
            <td class="conj-bucket">${renderGroupCell(groups.sing.active)}</td>
            <td class="conj-bucket">${renderGroupCell(groups.sing.stative)}</td>
            <td class="conj-bucket conj-bucket-side">${renderGroupCell(groups.sing.refl)}</td>
          </tr>
          <tr class="conj-group">
            <th class="conj-rowhead">Plural</th>
            <td class="conj-bucket">${renderGroupCell(groups.pl.active)}</td>
            <td class="conj-bucket">${renderGroupCell(groups.pl.stative)}</td>
            <td class="conj-bucket conj-bucket-side">${renderGroupCell(groups.pl.refl)}</td>
          </tr>
        </tbody>
      </table>
    `;
    htmlString += '</div>';
    return htmlString;
  }

  function renderBucket(items) {
    if (!items.length) {
      return '<div class="conj-empty">—</div>';
    }
    return items.map((item) => renderPairLine(item.subj, item.obj, item.conj, item.morphKind)).join('');
  }

  function renderControls(unId, negar) {
    return `
      <div class="conj-controls-bar">
        <div class="conj-controls">
          <label class="conj-controls-label" for="mode-${unId}">Modo</label>
          <select id="mode-${unId}" class="option">
            <!-- Add options dynamically using JavaScript -->
          </select>
        </div>
        <div class="conj-legend">
          <div class="conj-legend-title">Ordem: quem faz &gt; quem recebe</div>
          <br><div class="conj-legend-note">el@ = ele/ela/eles/elas/elus/isso</div>
          <br><div class="conj-legend-note">@s = o/a/os/as</div>
        </div>
        <label class="conj-toggle" for="negarCheckbox-${unId}">
          <input type="checkbox" id="negarCheckbox-${unId}" ${negar ? 'checked' : ''} name="negarCheckbox">
          <span>Negar</span>
        </label>
      </div>
    `;
  }

  function generateConjugationTableRanked({ mode, conjugations, subjectsVals, objectsVals, unId, negar }) {
    const showLabels = mode !== 'circunstancial' && mode !== 'conjuntivo';
    const buckets = {
      active: { '12': [], '123-3': [], refl: [], mut: [] },
      stative: { '12': [], '123-3': [], refl: [], mut: [] },
    };

    subjectsVals.forEach((subj) => {
      objectsVals.forEach((obj) => {
        const conj = conjugations[JSON.stringify([subj, obj])] || '-';
        if (!conj || conj === '-') return;
        const morphKind = getMorphKind(subj, obj);
        const group = morphKind === 'stative' ? 'stative' : 'active';
        const bucketKey = getBucketKey(subj, obj);
        if (!bucketKey) return;
        buckets[group][bucketKey].push({ subj, obj, conj, morphKind });
      });
    });

    const sortPairs = (a, b) => {
      const subjOrder = (PERSON_ORDER[a.subj] ?? 99) - (PERSON_ORDER[b.subj] ?? 99);
      if (subjOrder !== 0) return subjOrder;
      return (PERSON_ORDER[a.obj] ?? 99) - (PERSON_ORDER[b.obj] ?? 99);
    };

    buckets.active['12'].sort(sortPairs);
    buckets.active['123-3'].sort(sortPairs);
    buckets.active.refl.sort(sortPairs);
    buckets.active.mut.sort(sortPairs);
    buckets.stative['12'].sort(sortPairs);
    buckets.stative['123-3'].sort(sortPairs);
    buckets.stative.refl.sort(sortPairs);
    buckets.stative.mut.sort(sortPairs);

    const headWithLabel = (label, text) => (
      showLabels ? `<span class="conj-subhead-label">${label}</span> ${text}` : text
    );

    if (mode === 'circunstancial') {
      let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
      htmlString += renderControls(unId, negar);
      htmlString += `
        <table class="conj-rank-table">
          <colgroup>
            <col class="conj-col-main">
            <col class="conj-col-main">
            <col class="conj-col-side">
          </colgroup>
          <tbody>
            <tr class="conj-subhead is-active">
              <th>${headWithLabel('Ativa', '1 &gt; 2')}</th>
              <th>123 &gt; 3</th>
              <th class="conj-side-head">Reflexivo</th>
            </tr>
            <tr class="conj-group conj-group-active">
              <td class="conj-bucket conj-bucket-span" rowspan="3">${renderBucket(buckets.active['12'])}</td>
              <td class="conj-bucket">${renderBucket(buckets.active['123-3'])}</td>
              <td class="conj-bucket conj-bucket-side">${renderBucket(buckets.active.refl)}</td>
            </tr>
            <tr class="conj-subhead-lower is-stative">
              <td class="conj-subhead-cell">3 &gt; 12</td>
              <td class="conj-side-head">Mútuo</td>
            </tr>
            <tr class="conj-group conj-group-stative">
              <td class="conj-bucket conj-bucket-lower">${renderBucket(buckets.stative['123-3'])}</td>
              <td class="conj-bucket conj-bucket-side conj-bucket-lower">${renderBucket(buckets.active.mut)}</td>
            </tr>
          </tbody>
        </table>
      `;
      htmlString += '</div>';
      return htmlString;
    }

    let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
    htmlString += renderControls(unId, negar);
    htmlString += `
      <table class="conj-rank-table">
        <colgroup>
          <col class="conj-col-main">
          <col class="conj-col-main">
          <col class="conj-col-side">
        </colgroup>
        <tbody>
          <tr class="conj-subhead is-active">
            <th>${headWithLabel('Ativa', '1 &gt; 2')}</th>
            <th>123 &gt; 3</th>
            <th class="conj-side-head">Reflexivo</th>
          </tr>
          <tr class="conj-group conj-group-active">
            <td class="conj-bucket">${renderBucket(buckets.active['12'])}</td>
            <td class="conj-bucket">${renderBucket(buckets.active['123-3'])}</td>
            <td class="conj-bucket conj-bucket-side">${renderBucket(buckets.active.refl)}</td>
          </tr>
          <tr class="conj-divider">
            <td colspan="2"></td>
            <td class="conj-side-empty"></td>
          </tr>
          <tr class="conj-subhead is-stative">
            <th>${headWithLabel('Estativa', '2 &gt; 1')}</th>
            <th>3 &gt; 12</th>
            <th class="conj-side-head">Mútuo</th>
          </tr>
          <tr class="conj-group conj-group-stative">
            <td class="conj-bucket">${renderBucket(buckets.stative['12'])}</td>
            <td class="conj-bucket">${renderBucket(buckets.stative['123-3'])}</td>
            <td class="conj-bucket conj-bucket-side">${renderBucket(buckets.active.mut)}</td>
          </tr>
        </tbody>
      </table>
    `;
    htmlString += '</div>';
    return htmlString;
  }

  function generateConjugationTableIntransitive({
    conjugations,
    subjectsVals,
    objectsVals,
    unId,
    negar,
  }) {
    const obj = objectsVals.length ? objectsVals[0] : null;
    const lines = subjectsVals.map((subj) => {
      const conj = conjugations[JSON.stringify([subj, obj])] || '-';
      if (!conj || conj === '-') return '';
      return renderSubjectLine(subj, conj);
    }).filter(Boolean);

    let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
    htmlString += renderControls(unId, negar);
    htmlString += `
      <table class="conj-simple-table">
        <thead>
          <tr class="conj-subhead">
            <th><span class="conj-subhead-label">Sujeito</span></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="conj-bucket conj-bucket-simple">${lines.join('') || '<div class="conj-empty">—</div>'}</td>
          </tr>
        </tbody>
      </table>
    `;
    htmlString += '</div>';
    return htmlString;
  }

  function generateConjugationTableObjectOnly({
    conjugations,
    subjectsVals,
    objectsVals,
    unId,
    negar,
  }) {
    const lines = objectsVals.map((obj) => {
      let conj = '-';
      for (let i = 0; i < subjectsVals.length; i += 1) {
        const subj = subjectsVals[i];
        const found = conjugations[JSON.stringify([subj, obj])];
        if (found) {
          conj = found;
          break;
        }
      }
      if (!conj || conj === '-') return '';
      return renderObjectLine(obj, conj);
    }).filter(Boolean);

    let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
    htmlString += renderControls(unId, negar);
    htmlString += `
      <table class="conj-simple-table">
        <thead>
          <tr class="conj-subhead">
            <th><span class="conj-subhead-label">Objeto</span></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="conj-bucket conj-bucket-simple">${lines.join('') || '<div class="conj-empty">—</div>'}</td>
          </tr>
        </tbody>
      </table>
    `;
    htmlString += '</div>';
    return htmlString;
  }

  function renderPersonHeader(label, code, role, scope) {
    const meta = getPersonMeta(code, role);
    const scopeAttr = scope ? ` scope="${scope}"` : '';
    const rankChip = meta.rankSymbol ? `<span class="conj-rank">${meta.rankSymbol}</span>` : '';
    const ptLine = meta.pt ? `<div class="conj-pt">${meta.pt}</div>` : '';
    const termLine = meta.term ? `<div class="conj-term">${meta.term}</div>` : '';

    return `
      <th${scopeAttr} class="conj-person conj-person-${role}">
        <div class="conj-person-top">
          <span class="conj-person-form">${label}</span>
          ${rankChip}
        </div>
        <div class="conj-person-meta">
          ${ptLine}
          ${termLine}
        </div>
      </th>
    `;
  }

  function generateConjugationTableGrid({
    mode,
    conjugations,
    subjects,
    subjectsVals,
    objects,
    objectsVals,
    unId,
    negar,
  }) {
    let htmlString = `<div class="options-container conj-wrap" id="conj-${unId}">`;
    htmlString += renderControls(unId, negar);
    htmlString += `<table class="conj-table">
      <thead>
        <tr class="conj-header-row">
          <th class="conj-axis conj-axis-subj" scope="col">
            <div class="conj-axis-title">Sujeito</div>
            <div class="conj-axis-sub">Agente</div>
          </th>`;

    objects.forEach((object, index) => {
      htmlString += renderPersonHeader(object, objectsVals[index], 'obj', 'col');
    });

    htmlString += `</tr>
      </thead>
      <tbody>`;

    for (let i = 0; i < subjects.length; i++) {
      htmlString += '<tr>';
      htmlString += renderPersonHeader(subjects[i], subjectsVals[i], 'subj', 'row');
      const subj = subjectsVals[i];

      for (let j = 0; j < objects.length; j++) {
        const obj = objectsVals[j];
        const conj = conjugations[JSON.stringify([subj, obj])] || '-';
        const isEmpty = conj === '-' || conj === '';
        const morphKind = getMorphKind(subj, obj);
        const morphClass = morphKind ? `morph-${morphKind}` : '';
        const morphLabel = morphKind === 'active'
          ? 'ativo'
          : morphKind === 'stative'
            ? 'estativo'
            : morphKind === 'equal'
              ? 'igual'
              : '';

        htmlString += `
          <td class="conj-cell ${morphClass}${isEmpty ? ' is-empty' : ''}" data-morph="${morphKind}">
            <span class="sr-only">${morphLabel}</span>
            <div class="conj-form">${conj}</div>
          </td>
        `;
      }

      htmlString += '</tr>';
    }

    htmlString += '</tbody></table></div>';
    return htmlString;
  }

  function generateConjugationTable(mode, conjugationsRaw, unId, ne) {
    const negar = ne || false;
    const filteredConjugations = conjugationsRaw.filter((item) => item.m === mode.slice(0, 2));
    const uniqueSubjects = new Set(filteredConjugations.map((item) => item.s));
    const uniqueObjects = new Set(filteredConjugations.map((item) => item.o));
    const conjugations = transformConjList(mode, filteredConjugations, negar);

    let subjMap = SUBJ_PREF_MAP;
    let objMap = OBJ_PREF_MAP;

    if (mode === 'imperativo') {
      subjMap = {
        'endé': '2ps',
        'peẽ': '2pp',
      };
    } else if (mode === 'circunstancial') {
      subjMap = {
        'ø': null,
        'ixé': '1ps',
        'oré': '1ppe',
        'îandé': '1ppi',
        "a'e": '3p',
      };
    }

    const subjectPairs = Object.entries(subjMap)
      .filter((item) => uniqueSubjects.has(item[1]))
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => (PERSON_ORDER[a.value] ?? 99) - (PERSON_ORDER[b.value] ?? 99));

    const objectPairs = Object.entries(objMap)
      .filter((item) => uniqueObjects.has(item[1]))
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => (PERSON_ORDER[a.value] ?? 99) - (PERSON_ORDER[b.value] ?? 99));

    const subjectsVals = subjectPairs.map((item) => item.value);
    const subjects = subjectPairs.map((item) => item.label);
    const objectsVals = objectPairs.map((item) => item.value);
    const objects = objectPairs.map((item) => item.label);

    if (isIntransitive(objectsVals)) {
      return generateConjugationTableIntransitive({
        conjugations,
        subjectsVals,
        objectsVals,
        unId,
        negar,
      });
    }

    if (mode === 'gerundio') {
      return generateConjugationTableObjectOnly({
        conjugations,
        subjectsVals,
        objectsVals,
        unId,
        negar,
      });
    }

    if (mode === 'imperativo') {
      return generateConjugationTableImperative({
        conjugations,
        subjectsVals,
        objectsVals,
        unId,
        negar,
      });
    }

    return generateConjugationTableRanked({
      mode,
      conjugations,
      subjectsVals,
      objectsVals,
      unId,
      negar,
    });
  }

  function populateDropdown(dropdown, options, mode) {
    if (!dropdown) return;

    options.forEach((option) => {
      const optionElement = document.createElement('option');
      optionElement.value = option;
      optionElement.text = option;
      dropdown.add(optionElement);
    });
    dropdown.value = mode;
  }

  function createConjugateFunction(tableElement, conjugations) {
    if (!tableElement) return;

    const negarCheckbox = tableElement.querySelector('input[type="checkbox"]');
    const selectElement = tableElement.querySelector('select');
    if (!negarCheckbox || !selectElement) return;

    function appendFValue() {
      const modeValue = selectElement.value;
      appendOptionsToResultDiv(tableElement.parentElement, conjugations, modeValue, negarCheckbox.checked);
      tableElement.remove();
    }

    selectElement.addEventListener('change', appendFValue);
    negarCheckbox.addEventListener('change', appendFValue);
  }

  function appendOptionsToResultDiv(resultDiv, conjugations, mode, ne) {
    const unId = Math.random().toString(36).substring(2, 10);
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = generateConjugationTable(mode, conjugations, unId, ne);

    const storedState = getCookie('conjugationToggle');
    if (storedState === 'enabled') {
      tempContainer.firstChild.style.display = 'block';
    } else {
      tempContainer.firstChild.style.display = 'none';
    }

    const tableElement = tempContainer.firstElementChild;
    if (!tableElement) return;

    resultDiv.appendChild(tableElement);
    populateDropdown(tableElement.querySelector('select'), MODES, mode);
    createConjugateFunction(tableElement, conjugations);
  }

  function linkSources(definition) {
    let replacedString = definition;

    // VLB
    let regex = /VLB, (I|II), (\d+)/g;
    replacedString = replacedString.replace(regex, (match, p1, p2) => {
      if (p1 === 'II') {
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=vlb&page_number=${parseInt(p2, 10) + 154}" target="_blank">${match}</a>`;
      }
      return `<a href="/nhe-enga/docs/primary_sources/?book_name=vlb&page_number=${p2}" target="_blank">${match}</a>`;
    });

    // Anchieta Arte
    regex = /Anch\., Arte, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, p1) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=ancharte&page_number=${p1}" target="_blank">${match}</a>`
    ));

    // Araujo Cat 1618
    regex = /Ar\., Cat\., (?!1686)(\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, p1) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=arcat1618&page_number=${p1}" target="_blank">${match}</a>`
    ));

    // Bettendorf compendio
    regex = /Bettendorff, Compêndio, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, p1) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=betcomp&page_number=${Number(p1) + 9}" target="_blank">${match}</a>`
    ));

    // Lery Histoire
    regex = /L(é|e)ry, Histoire, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, _p1, p2) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=lerhist&page_number=${Number(p2) + (341 - 287)}" target="_blank">${match}</a>`
    ));

    return replacedString;
  }

  function splitByBullet(text) {
    const parts = [];
    let current = '';
    let parenDepth = 0;

    for (let idx = 0; idx < text.length; idx += 1) {
      const ch = text[idx];
      if (ch === '(') {
        parenDepth += 1;
      } else if (ch === ')' && parenDepth > 0) {
        parenDepth -= 1;
      }

      if (ch === '●' && parenDepth === 0) {
        parts.push(current.trim());
        current = '';
        continue;
      }

      current += ch;
    }

    if (current.trim()) {
      parts.push(current.trim());
    }

    return parts;
  }

  function splitByNota(text) {
    let parenDepth = 0;
    const upper = text.toUpperCase();
    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      if (char === '(') {
        parenDepth += 1;
      } else if (char === ')' && parenDepth > 0) {
        parenDepth -= 1;
      }

      if (parenDepth === 0 && upper.startsWith('NOTA', i)) {
        const prev = upper[i - 1] || '';
        const next = upper[i + 4] || '';
        const boundaryPrev = !/[A-ZÀ-Ý]/.test(prev);
        const boundaryNext = !/[A-ZÀ-Ý]/.test(next);
        if (boundaryPrev && boundaryNext) {
          return {
            before: text.slice(0, i).trim(),
            nota: text.slice(i).trim(),
          };
        }
      }
    }

    return { before: text, nota: '' };
  }

  function linkRelatedHeadwords(section) {
    let output = '';
    let i = 0;
    let parenDepth = 0;
    let atEntryStart = true;
    const len = section.length;

    const isLetterStart = (char) => char && TUPI_LETTER_RE.test(char);
    const isHeadChar = (char) => char && TUPI_HEAD_CHAR_RE.test(char);

    while (i < len) {
      const char = section[i];

      if (char === '(') {
        parenDepth += 1;
      } else if (char === ')' && parenDepth > 0) {
        parenDepth -= 1;
      }

      if (parenDepth === 0 && atEntryStart) {
        let j = i;
        while (j < len && /\s/.test(section[j])) {
          j += 1;
        }

        if (j < len && isLetterStart(section[j])) {
          let k = j + 1;
          while (k < len && isHeadChar(section[k])) {
            k += 1;
          }

          const findDashAfterMeta = (pos) => {
            let t = pos;
            while (t < len && /\s/.test(section[t])) {
              t += 1;
            }
            // Skip parenthetical metadata like (t, t)
            while (t < len && (section[t] === '(' || section[t] === '[')) {
              let depth = 0;
              const openChar = section[t];
              const closeChar = openChar === '(' ? ')' : ']';
              let u = t;
              while (u < len) {
                if (section[u] === openChar) depth += 1;
                else if (section[u] === closeChar) {
                  depth -= 1;
                  if (depth === 0) {
                    u += 1;
                    break;
                  }
                }
                u += 1;
              }
              t = u;
              while (t < len && /\s/.test(section[t])) {
                t += 1;
              }
            }
            return section.slice(t).match(/^-\s/) ? t : -1;
          };

          let bestEnd = -1;
          let tempEnd = k;

          while (tempEnd <= len) {
            const dashPos = findDashAfterMeta(tempEnd);
            if (dashPos !== -1) {
              bestEnd = tempEnd;
            }

            let nextPos = tempEnd;
            while (nextPos < len && /\s/.test(section[nextPos])) {
              nextPos += 1;
            }
            if (nextPos >= len || !isLetterStart(section[nextPos])) {
              break;
            }

            let nextEnd = nextPos + 1;
            while (nextEnd < len && isHeadChar(section[nextEnd])) {
              nextEnd += 1;
            }
            tempEnd = nextEnd;
          }

          if (bestEnd !== -1) {
            const headword = section.slice(j, bestEnd);
            const headwordUpper = headword.toUpperCase();
            if (headwordUpper !== 'NOTA') {
              output += section.slice(i, j);
              output += `<span class="related-entry-headword"><a href="${window.location.pathname}?query=${encodeURIComponent(headword)}" class="search-link related-link">${headword}</a></span>`;
              i = bestEnd;
              atEntryStart = false;
              continue;
            }
          }
        }
      }

      output += char;

      if (parenDepth === 0 && (char === ';' || char === '●')) {
        atEntryStart = true;
      } else if (!/\s/.test(char)) {
        atEntryStart = false;
      }

      i += 1;
    }

    return output;
  }

  function formatVerbeteSection(section) {
    let output = '';
    let i = 0;
    let parenDepth = 0;
    let expectedNumber = 1;
    let expectedLetter = 'a';
    let seenNumber = false;
    let definitionOpen = false;
    let inDialogueSegment = false;

    const isBoundary = (char) => char === undefined || /[\s.;:!?]/.test(char);
    const sectionLabelMap = {
      'adj.': 'Adjetivo',
      'adv.': 'Advérbio',
    };
    const extractSectionLabel = () => {
      const match = output.match(/(\s*\((adj\.|adv\.)\)\s*-\s*)$/i);
      if (!match) return '';
      output = output.slice(0, -match[1].length);
      return match[2].toLowerCase();
    };
    const extractSensePrefix = () => {
      const match = output.match(/(\s*\(([^)]+)\)\s*-\s*)$/);
      if (!match) return '';
      output = output.slice(0, -match[1].length);
      return `(${match[2]}) `;
    };
    const segments = [];

    while (i < section.length) {
      const char = section[i];

      if (parenDepth === 0) {
        const labelMatch = section.slice(i).match(/^\((adj\.|adv\.)\)\s*-\s*/i);
        if (labelMatch) {
          let lookahead = i + labelMatch[0].length;
          while (lookahead < section.length && /\s/.test(section[lookahead])) {
            lookahead += 1;
          }
          const nextChar = section[lookahead];
          const hasNumberAhead = nextChar && /\d/.test(nextChar);

          if (!hasNumberAhead) {
            if (definitionOpen) {
              output += '</span>';
              definitionOpen = false;
            }
            if (output.length && !output.endsWith('<br>')) {
              output += '<br>';
            }
            const labelKey = labelMatch[1].toLowerCase();
            if (sectionLabelMap[labelKey]) {
              output += `<div class="sense-section-title">${sectionLabelMap[labelKey]}:</div>`;
            }
            output += '<span class="sense-definition">';
            definitionOpen = true;
            expectedNumber = 1;
            expectedLetter = 'a';
            seenNumber = false;
            i += labelMatch[0].length;
            continue;
          }
        }

        const prevChar = section[i - 1];
        const nextChar = section[i + 1];
        const boundaryOk = isBoundary(prevChar);

        if (boundaryOk) {
          const numberMatch = section.slice(i).match(/^(\d+)\)/);
          if (numberMatch) {
            const numberValue = Number(numberMatch[1]);
            const sectionKey = extractSectionLabel();
            if (sectionKey && numberValue === 1 && sectionLabelMap[sectionKey]) {
              if (definitionOpen) {
                output += '</span>';
                definitionOpen = false;
              }
              if (output.length && !output.endsWith('<br>')) {
                output += '<br>';
              }
              output += `<div class="sense-section-title">${sectionLabelMap[sectionKey]}:</div>`;
              expectedNumber = 1;
              expectedLetter = 'a';
              seenNumber = true;
            }
            if (Number.isFinite(numberValue) && numberValue === expectedNumber) {
              if (definitionOpen) {
                output += '</span>';
                definitionOpen = false;
              }
              const trimmedOutput = output.trim();
              if (output.length && !output.endsWith('<br>') && !trimmedOutput.endsWith(':')) {
                output += '<br>';
              }
              const sensePrefix = extractSensePrefix();
              output += `<span class="sense-number">${numberMatch[0]}</span>`;
              output += '<span class="sense-definition">';
              output += sensePrefix;
              definitionOpen = true;
              expectedNumber += 1;
              expectedLetter = 'a';
              seenNumber = true;
              i += numberMatch[0].length;
              continue;
            }
          }

          const letterMatch = section.slice(i).match(/^([a-z])\)/i);
          if (letterMatch && seenNumber) {
            const letterValue = letterMatch[1].toLowerCase();
            if (letterValue === expectedLetter) {
              if (definitionOpen) {
                output += '</span>';
                definitionOpen = false;
              }
              const trimmedOutput = output.trim();
              if (output.length && !output.endsWith('<br>') && !trimmedOutput.endsWith(':')) {
                output += '<br>';
              }
              const sensePrefix = extractSensePrefix();
              output += `<span class="sense-letter">${letterMatch[0]}</span>`;
              output += '<span class="sense-definition">';
              output += sensePrefix;
              definitionOpen = true;
              expectedLetter = String.fromCharCode(expectedLetter.charCodeAt(0) + 1);
              i += letterMatch[0].length;
              continue;
            }
          }
        }
      }

      if (
        parenDepth === 0 &&
        char === '-' &&
        TUPI_LETTER_RE.test(section[i + 1]) &&
        /\s/.test(section[i - 1] || '')
      ) {
        if (!inDialogueSegment) {
          inDialogueSegment = true;
          if (output.trim().length > 0) {
            segments.push(output);
            output = '';
            continue;
          }
        }
      }

      if (definitionOpen && parenDepth === 0 && char === ':') {
        output += '</span>';
        definitionOpen = false;
        output += char;
        i += 1;
        continue;
      }

      if (char === ';' && parenDepth === 0) {
        if (definitionOpen) {
          output += '</span>';
          definitionOpen = false;
        }
        output += char;
        segments.push(output);
        output = '';
        inDialogueSegment = false;
        i += 1;
        continue;
      }

      output += char;
      if (char === '(') {
        parenDepth += 1;
      } else if (char === ')' && parenDepth > 0) {
        parenDepth -= 1;
      }
      i += 1;
    }

    if (definitionOpen) {
      output += '</span>';
      definitionOpen = false;
    }

    if (output) {
      segments.push(output);
    }

    const normalizeQuoteText = (text) => text.trim().replace(/[;]+$/g, '').trim();
    const quoteStartRe = /^(\"|“|”|'|‘|’|\\.\\.\\.|…)/;
    const stripTags = (text) => text.replace(/<[^>]*>/g, '');
    const countDash = (text) => (text.match(/\s-\s/g) || []).length;

    const hasDash = (text) => /\s-\s/.test(normalizeQuoteText(text));
    const hasCitation = (text) => /\([^()]*\)/.test(normalizeQuoteText(text));
    const hasTrailingCitation = (text) => /\([^()]*\d[^()]*\)\s*$/.test(normalizeQuoteText(text));

    const extractTrailingCitation = (text) => {
      const trimmed = normalizeQuoteText(text);
      if (!trimmed.endsWith(')')) {
        return { body: trimmed, citation: '' };
      }

      let depth = 0;
      for (let idx = trimmed.length - 1; idx >= 0; idx -= 1) {
        const ch = trimmed[idx];
        if (ch === ')') {
          depth += 1;
          continue;
        }
        if (ch === '(') {
          depth -= 1;
          if (depth === 0) {
            return {
              body: trimmed.slice(0, idx).trim(),
              citation: trimmed.slice(idx).trim(),
            };
          }
        }
      }

      return { body: trimmed, citation: '' };
    };

    const splitQuoteLines = (text) => {
      const { body, citation } = extractTrailingCitation(text);
      const dashIndex = body.indexOf(' - ');
      if (dashIndex === -1) {
        const trimmedBody = body.trim();
        if (quoteStartRe.test(trimmedBody)) {
          return { tupi: '', pt: body, citation };
        }
        return { tupi: body, pt: '', citation };
      }

      return {
        tupi: body.slice(0, dashIndex).trim(),
        pt: body.slice(dashIndex + 3).trim(),
        citation,
      };
    };

    const splitDialogueSegments = (text) => {
      const segments = [];
      let start = -1;
      const len = text.length;

      for (let idx = 0; idx < len; idx += 1) {
        const char = text[idx];
        const nextChar = text[idx + 1];
        const prevChar = text[idx - 1];
        const isDialogueStart = char === '-' && TUPI_LETTER_RE.test(nextChar) && (idx === 0 || /\s/.test(prevChar));
        if (isDialogueStart) {
          if (start !== -1) {
            const slice = text.slice(start, idx).trim();
            if (slice) segments.push(slice);
          }
          start = idx;
        }
      }

      if (start !== -1) {
        const slice = text.slice(start).trim();
        if (slice) segments.push(slice);
      }

      return segments.map((segment) => segment.replace(TUPI_DIALOGUE_LEAD_RE, (match) => match.slice(1)).trim()).filter(Boolean);
    };

    const parseDialogue = (text) => {
      const normalized = normalizeQuoteText(text);
      if (!TUPI_DIALOGUE_RE.test(normalized)) {
        return null;
      }

      const { body, citation } = extractTrailingCitation(normalized);
      const segments = splitDialogueSegments(body);
      if (segments.length < 4 || segments.length % 2 !== 0) {
        return null;
      }

      const midpoint = segments.length / 2;
      return {
        tupiLines: segments.slice(0, midpoint),
        ptLines: segments.slice(midpoint),
        citation,
      };
    };

    const buildDialogueBlock = (tupiLines, ptLines, citation) => {
      const maxLines = Math.max(tupiLines.length, ptLines.length);
      const rows = [];
      for (let index = 0; index < maxLines; index += 1) {
        const tupi = tupiLines[index] || '';
        const pt = ptLines[index] || '';
        const icon = index % 2 === 0 ? '💬' : '🗨️';
        const citationHtml = index === maxLines - 1 && citation
          ? ` <span class="quote-citation">${citation}</span>`
          : '';
        rows.push(`
          <div class="dialogue-line ${index % 2 === 0 ? 'speaker-a' : 'speaker-b'}">
            <div class="dialogue-tupi"><span class="dialogue-icon" aria-hidden="true">${icon}</span> ${tupi}</div>
            <div class="dialogue-pt">${pt}${citationHtml}</div>
          </div>
        `);
      }

      return `<div class="sense-quote dialogue">${rows.join('')}</div>`;
    };

    const stripLeadingDashSpace = (value) => value.replace(/^\s*-\s+/, '');

    const buildQuoteBlock = (text) => {
      const dialogue = parseDialogue(text);
      if (dialogue) {
        return buildDialogueBlock(dialogue.tupiLines, dialogue.ptLines, dialogue.citation);
      }

      let { tupi, pt, citation } = splitQuoteLines(text);
      tupi = stripLeadingDashSpace(tupi);
      pt = stripLeadingDashSpace(pt);
      const citationHtml = citation ? ` <span class="quote-citation">${citation}</span>` : '';
      const tupiLine = tupi ? `<div class="quote-tupi">${tupi}${!pt ? citationHtml : ''}</div>` : '';
      const ptLine = pt ? `<div class="quote-pt">${pt}${citationHtml}</div>` : '';
      const citationLine = !pt && !tupi && citation ? `<div class="quote-citation">${citation}</div>` : '';

      return `<div class="sense-quote">${tupiLine}${ptLine}${citationLine}</div>`;
    };

    const findColonOutside = (text) => {
      let inTag = false;
      let depth = 0;
      for (let idx = 0; idx < text.length; idx += 1) {
        const ch = text[idx];
        if (ch === '<') {
          inTag = true;
          continue;
        }
        if (ch === '>' && inTag) {
          inTag = false;
          continue;
        }
        if (inTag) continue;
        if (ch === '(') {
          depth += 1;
          continue;
        }
        if (ch === ')' && depth > 0) {
          depth -= 1;
          continue;
        }
        if (ch === ':' && depth === 0) {
          return idx;
        }
      }
      return -1;
    };

    const mergeQuotedSegments = (items) => {
      const merged = [];
      let idx = 0;

      while (idx < items.length) {
        const segment = items[idx];
        const trimmed = stripTags(segment).trim();

        if (!hasTrailingCitation(trimmed)) {
          let combined = segment;
          let j = idx + 1;
          let foundCitation = false;

          while (j < items.length) {
            combined += items[j];
            const combinedPlain = stripTags(combined).trim();
            if (hasTrailingCitation(combinedPlain)) {
              foundCitation = true;
              break;
            }
            j += 1;
          }

          if (foundCitation) {
            const combinedPlain = stripTags(combined).trim();
            const dashCount = countDash(combinedPlain);
            const startsWithQuote = quoteStartRe.test(trimmed);
            const hasDash = dashCount > 0;
            const shouldMerge = (startsWithQuote && dashCount <= 1) || (hasDash && dashCount === 1);

            if (shouldMerge) {
              merged.push(combined);
              idx = j + 1;
              continue;
            }
          }
        }

        merged.push(segment);
        idx += 1;
      }

      return merged;
    };

    const parseSegment = (segment) => {
      const brMatch = segment.match(/^((?:<br>)+)(.*)$/i);
      const brPrefix = brMatch ? brMatch[1] : '';
      const remainder = brMatch ? brMatch[2] : segment;
      const spacingMatch = remainder.match(/^(\s*)(.*?)(\s*)$/s);
      const leadingSpace = spacingMatch ? spacingMatch[1] : '';
      const core = spacingMatch ? spacingMatch[2] : remainder;
      const trailingSpace = spacingMatch ? spacingMatch[3] : '';
      const plainCore = stripTags(core);
      const trimmedCore = core.trim();
      const startsWithHeadwordLink = trimmedCore.startsWith('<span class="related-entry-headword">');
      const startsWithDialogue = TUPI_DIALOGUE_RE.test(trimmedCore);

      const colonIndex = findColonOutside(core);
      if (colonIndex !== -1) {
        let left = core.slice(0, colonIndex + 1);
        let right = core.slice(colonIndex + 1).trim();
        let plainRight = stripTags(right);

        const startsWithSenseMarker = (() => {
          if (plainRight.trim().match(/^(\d+|[a-z])\)/i)) {
            return true;
          }
          return /<span class="sense-(number|letter)">/i.test(right);
        })();

        if (startsWithSenseMarker) {
          const secondaryIndex = findColonOutside(right);
          if (secondaryIndex !== -1) {
            const newColonPos = colonIndex + 1 + secondaryIndex;
            const candidateRight = core.slice(newColonPos + 1).trim();
            const candidatePlainRight = stripTags(candidateRight);
            const candidateStartsDialogue = TUPI_DIALOGUE_RE.test(candidatePlainRight.trim());
            if (candidateRight && (hasDash(candidatePlainRight) || candidateStartsDialogue)) {
              left = core.slice(0, newColonPos + 1);
              right = candidateRight;
              plainRight = candidatePlainRight;
            }
          }
        }

        const rightStartsDialogue = TUPI_DIALOGUE_RE.test(plainRight.trim());
        if (right && (hasDash(plainRight) || rightStartsDialogue)) {
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'colonQuote',
            left,
            quoteText: right,
            startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
          };
        }
      }

      if (startsWithDialogue) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'dialogue',
          quoteText: trimmedCore,
          startsWithLetter: TUPI_START_RE.test(trimmedCore),
        };
      }

      if (hasDash(plainCore)) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'quote',
          quoteText: core.trim(),
          startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
        };
      }

      if (hasTrailingCitation(plainCore) && quoteStartRe.test(plainCore.trim())) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'quote',
          quoteText: core.trim(),
          startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
        };
      }

      return {
        segment,
        brPrefix,
        leadingSpace,
        core,
        trailingSpace,
        plainCore,
        startsWithHeadwordLink,
        type: 'other',
        quoteText: '',
        startsWithLetter: false,
      };
    };

    const mergedSegments = mergeQuotedSegments(segments);
    const parsedSegments = mergedSegments.map(parseSegment);

    parsedSegments.forEach((seg) => {
      const plain = (seg.plainCore || '').trim();
      if (!plain || seg.startsWithHeadwordLink) return;
      if (seg.type === 'other' && /\s-\s/.test(plain)) {
        warnOnce('Unparsed quote-like segment', plain);
      }
      if (seg.type === 'other' && hasTrailingCitation(plain)) {
        warnOnce('Unparsed trailing citation segment', plain);
      }
    });

    const ensureCitation = (text, startIndex) => {
      const normalized = normalizeQuoteText(text);
      const { citation } = extractTrailingCitation(normalized);
      if (citation) {
        return normalized;
      }

      for (let idx = startIndex; idx < parsedSegments.length; idx += 1) {
        const next = parsedSegments[idx];
        if (next.type === 'quote') {
          const nextNormalized = normalizeQuoteText(next.quoteText);
          const { citation: nextCitation } = extractTrailingCitation(nextNormalized);
          if (nextCitation) {
            return `${normalized} ${nextCitation}`;
          }
          continue;
        }
        break;
      }

      return normalized;
    };

    let inQuoteList = false;
    let seenContent = false;
    const formattedSegments = [];

    for (let idx = 0; idx < parsedSegments.length; idx += 1) {
      const seg = parsedSegments[idx];

      if (seg.startsWithHeadwordLink) {
        inQuoteList = false;
      }

      if (seg.type === 'colonQuote') {
        inQuoteList = true;
        const quoteText = ensureCitation(seg.quoteText, idx + 1);
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlock(quoteText)}${seg.trailingSpace}`
        );
        seenContent = true;
        continue;
      }

      if (inQuoteList) {
        if ((seg.type === 'quote' || seg.type === 'dialogue') && !seg.startsWithHeadwordLink) {
          const quoteText = ensureCitation(seg.quoteText, idx + 1);
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlock(quoteText)}${seg.trailingSpace}`
          );
          continue;
        }
        inQuoteList = false;
      }

      if ((seg.type === 'dialogue' || seg.type === 'quote') && !seg.startsWithHeadwordLink) {
        const trimmedQuote = seg.quoteText.trim();
        if (TUPI_DIALOGUE_RE.test(trimmedQuote)) {
          const quoteText = ensureCitation(seg.quoteText, idx + 1);
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlock(quoteText)}${seg.trailingSpace}`
          );
          seenContent = true;
          continue;
        }
      }

      if (!seenContent && seg.type === 'quote' && seg.startsWithLetter && hasCitation(seg.quoteText) && !seg.startsWithHeadwordLink) {
        const quoteText = normalizeQuoteText(seg.quoteText);
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlock(quoteText)}${seg.trailingSpace}`
        );
        seenContent = true;
        continue;
      }

      formattedSegments.push(seg.segment);
      if (seg.plainCore.trim()) {
        seenContent = true;
      }
    }

    return formattedSegments.join('');
  }

  function formatVerbeteDefinition(definition) {
    const { before, nota } = splitByNota(definition);
    const sections = splitByBullet(before);
    if (sections.length <= 1) {
      const formatted = formatVerbeteSection(before);
      return nota ? `${formatted}<br>${nota}` : formatted;
    }

    const formattedMain = sections
      .map((section, index) => {
        let sectionWithLinks = index === 0 ? section : linkRelatedHeadwords(section);
        if (index !== 0) {
          sectionWithLinks = sectionWithLinks.replace(/^\s*(<br>\s*)+/, '');
        }
        const formattedSection = formatVerbeteSection(sectionWithLinks);
        if (index === 0) {
          return formattedSection;
        }
        const formattedWithBreaks = formattedSection.replace(/;\s*/g, ';<br>');
        return `<div class="sense-section-title">Verbetes relacionados:</div>${formattedWithBreaks}`;
      })
      .join('');

    return nota ? `${formattedMain}<br>${nota}` : formattedMain;
  }

  function toggleContent(event, link) {
    event.preventDefault();
    const preview = link.previousElementSibling;
    preview.classList.toggle('expanded');

    link.textContent = preview.classList.contains('expanded')
      ? 'Mostrar menos...'
      : 'Mostrar mais...';

    link.classList.toggle('is-less', preview.classList.contains('expanded'));
  }

  function updateShowMoreLinks() {
    const entries = document.querySelectorAll('.entry');

    entries.forEach((entry) => {
      const preview = entry.querySelector('.preview');
      const showMoreLink = entry.querySelector('.show-more');

      if (preview.scrollHeight > preview.clientHeight) {
        showMoreLink.style.display = 'inline';
      } else {
        showMoreLink.style.display = 'none';
      }
    });
  }

  function updateRetainQueryLinks() {
    const links = document.querySelectorAll('.retain-query');
    const currentQuery = window.location.search;

    links.forEach((link) => {
      link.href = link.href.split('?')[0];
      if (currentQuery) {
        link.href += currentQuery;
      }
    });
  }

  function toggleAllOptionsContainers(dry) {
    const isDry = dry || false;
    if (!isDry) {
      const optionsContainers = document.querySelectorAll('.options-container');

      optionsContainers.forEach((optionsContainer) => {
        const showValue = optionsContainer.tagName === 'TABLE' ? 'table' : 'block';
        optionsContainer.style.display =
          optionsContainer.style.display === 'none' || optionsContainer.style.display === '' ? showValue : 'none';
      });
    }

    toggleContainer.classList.toggle('disabled');

    const newPosition = !toggleContainer.classList.contains('disabled') ? '100%' : '0';
    toggleBall.style.transform = `translate(${newPosition}, -50%)`;
    setCookie('conjugationToggle', toggleContainer.classList.contains('disabled') ? 'disabled' : 'enabled', 30);
  }

  function highlightMatches(container, query) {
    if (!query) return;
    const normalizedQuery = stripDiacritics(query);
    if (!normalizedQuery) return;

    const buildNormalizedMap = (text) => {
      let normalized = '';
      const map = [];
      for (let idx = 0; idx < text.length; idx += 1) {
        const stripped = stripDiacritics(text[idx]);
        if (!stripped) continue;
        for (let j = 0; j < stripped.length; j += 1) {
          normalized += stripped[j];
          map.push(idx);
        }
      }
      return { normalized, map };
    };

    const rangesForText = (text) => {
      const { normalized, map } = buildNormalizedMap(text);
      if (!normalized) return [];
      const regex = new RegExp(escapeRegExp(normalizedQuery), 'ig');
      const ranges = [];
      let match;
      while ((match = regex.exec(normalized)) !== null) {
        const startNorm = match.index;
        const endNorm = startNorm + match[0].length - 1;
        const start = map[startNorm];
        const end = map[endNorm] + 1;
        if (start !== undefined && end !== undefined) {
          ranges.push([start, end]);
        }
        if (match.index === regex.lastIndex) {
          regex.lastIndex += 1;
        }
      }
      if (!ranges.length) return [];

      ranges.sort((a, b) => a[0] - b[0]);
      const merged = [ranges[0]];
      for (let i = 1; i < ranges.length; i += 1) {
        const last = merged[merged.length - 1];
        const current = ranges[i];
        if (current[0] <= last[1]) {
          last[1] = Math.max(last[1], current[1]);
        } else {
          merged.push(current);
        }
      }
      return merged;
    };

    const walker = document.createTreeWalker(
      container,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          if (!node.nodeValue || !node.nodeValue.trim()) {
            return NodeFilter.FILTER_REJECT;
          }
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          if (parent.closest('.highlighted')) return NodeFilter.FILTER_REJECT;
          if (parent.closest('.quote-citation')) return NodeFilter.FILTER_REJECT;
          if (parent.closest('script, style')) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      },
      false
    );

    const nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    nodes.forEach((node) => {
      const text = node.nodeValue;
      const ranges = rangesForText(text);
      if (!ranges.length) return;

      const fragment = document.createDocumentFragment();
      let lastIndex = 0;
      ranges.forEach(([start, end]) => {
        if (start > lastIndex) {
          fragment.appendChild(document.createTextNode(text.slice(lastIndex, start)));
        }
        const span = document.createElement('span');
        span.className = 'highlighted';
        span.textContent = text.slice(start, end);
        fragment.appendChild(span);
        lastIndex = end;
      });

      if (lastIndex < text.length) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
      }

      node.parentNode.replaceChild(fragment, node);
    });
  }

  function renderResults(results, query) {
    resultsDiv.style.display = 'block';

    if (!results.length) {
      resultsDiv.textContent = 'Não foram encontrados resultados.';
      return;
    }

    const fragment = document.createDocumentFragment();

    results.forEach((result) => {
      const entry = document.createElement('div');
      entry.classList.add('entry');

      const preview = document.createElement('div');
      preview.classList.add('preview');
      if (result.type !== undefined) {
        preview.classList.add(result.type);
      }

      const baseDefinition = result.is_tupi_portuguese
        ? formatVerbeteDefinition(result.definition)
        : result.definition;
      const linkedDefinition = linkSources(baseDefinition);

      const link = document.createElement('a');
      link.href = `${window.location.pathname}?query=${encodeURIComponent(result.first_word)}`;
      link.innerText = result.first_word;
      link.classList.add('search-link');

      const optionalNumberSup = document.createElement('sup');
      optionalNumberSup.innerText = result.optional_number;

      preview.appendChild(link);
      preview.appendChild(optionalNumberSup);
      preview.innerHTML += ` ${linkedDefinition}`;
      highlightMatches(preview, query);

      if (result.exact_match) {
        preview.classList.add('exact-match');
      } else {
        preview.classList.add('approximate-match');
      }

      entry.appendChild(preview);

      const showMore = document.createElement('a');
      showMore.classList.add('show-more');
      showMore.style.display = 'none';
      showMore.addEventListener('click', (event) => {
        toggleContent(event, showMore);
      });
      showMore.textContent = 'Mostrar mais...';
      entry.appendChild(showMore);

      if (result.con) {
        appendOptionsToResultDiv(preview, result.con, 'indicativo', false);
      }

      fragment.appendChild(entry);
    });

    resultsDiv.replaceChildren(fragment);
  }

  function performSearch(options = {}) {
    const { updateHistory = true } = options;
    if (!dataReady) {
      resultsDiv.textContent = 'Carregando dados...';
      return;
    }

    const query = searchInput.value.trim();
    const queryLower = query.toLowerCase();

    if (!query) {
      alert('Ops, é necessário preencher algo para pesquisar!');
      return;
    }

    const verbeteResultsExact = searchByFirstWord(searchIndex, query);
    const defResultsExact = searchAllDefinitions(searchIndex, queryLower);
    const verbeteResultsIn = searchInFirstWord(searchIndex, query);

    const verbeteResultsDiacritic = searchByFirstWordNoAccent(searchIndex, query);
    const defResultsDiacritic = searchAllDefinitionsNoAccent(searchIndex, query);
    const defResultsNoBounds = searchAllDefinitionsNoBounds(searchIndex, query);

    const combinedEntries = [
      ...verbeteResultsExact,
      ...verbeteResultsDiacritic,
      ...defResultsExact,
      ...verbeteResultsIn,
      ...defResultsDiacritic,
      ...defResultsNoBounds,
    ];

    const exactKeySet = new Set([
      ...verbeteResultsExact,
      ...defResultsExact,
    ].map((entry) => keyForItem(entry.item)));

    const seenKeys = new Set();
    const results = [];

    combinedEntries.forEach((entry) => {
      const key = keyForItem(entry.item);
      if (!seenKeys.has(key)) {
        seenKeys.add(key);
        results.push({
          ...entry.item,
          exact_match: exactKeySet.has(key),
        });
      }
    });

    renderResults(results, query);

    if (updateHistory) {
      const newUrl = `${window.location.pathname}?query=${encodeURIComponent(queryLower)}`;
      history.pushState(null, null, newUrl);
    }

    updateShowMoreLinks();
    updateRetainQueryLinks();
  }

  function handlePopstate() {
    const urlParams = new URLSearchParams(window.location.search);
    const queryParam = urlParams.get('query');

    if (queryParam) {
      searchInput.value = queryParam;
      performSearch({ updateHistory: false });
    }
  }

  function setCookie(name, value, days) {
    let expires = '';
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = `; expires=${date.toUTCString()}`;
    }
    document.cookie = `${name}=${value}${expires}; path=/`;
  }

  function getCookie(name) {
    const nameEQ = `${name}=`;
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  }

  async function loadData() {
    const [compressedRaw, neos] = await Promise.all([
      fetchCompressedJSON(DATA_PATH),
      fetchNeoCSV(NEO_PATH),
    ]);

    const compressedData = mapCompressedData(compressedRaw);
    const neoData = neos.map((item) => ({
      ...item,
      is_tupi_portuguese: true,
    }));
    jsonData = [...compressedData, ...neoData];
    searchIndex = buildSearchIndex(jsonData);
    window.jsonData = jsonData;
    dataReady = true;
  }

  function initEvents() {
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        performSearch();
      }
    });

    toggleContainer.addEventListener('click', () => {
      toggleAllOptionsContainers();
    });

    window.addEventListener('resize', updateShowMoreLinks);
    window.addEventListener('orientationchange', updateShowMoreLinks);
    window.addEventListener('popstate', handlePopstate);

    document.addEventListener('click', (event) => {
      if (event.target.classList.contains('search-link')) {
        event.preventDefault();
        searchInput.value = event.target.innerText;
        performSearch();
        window.scrollTo(0, 0);
      }
    });
  }

  async function init() {
    initEvents();
    updateRetainQueryLinks();

    try {
      searchButton.disabled = true;
      searchInput.disabled = true;
      resultsDiv.textContent = 'Carregando dados...';

      await loadData();

      searchButton.disabled = false;
      searchInput.disabled = false;
      resultsDiv.textContent = '';

      const urlParams = new URLSearchParams(window.location.search);
      const queryParam = urlParams.get('query');
      if (queryParam) {
        searchInput.value = queryParam;
        performSearch({ updateHistory: false });
      }
    } catch (error) {
      console.error(error);
      resultsDiv.textContent = 'Falha ao carregar dados. Recarregue a pagina.';
    }

    searchInput.focus();
  }

  document.addEventListener('DOMContentLoaded', () => {
    const storedState = getCookie('conjugationToggle');
    if (storedState === 'enabled') {
      toggleAllOptionsContainers(true);
    }
  });

  init();
})();
