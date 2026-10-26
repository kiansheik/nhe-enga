(() => {
  'use strict';

  const DATA_PATH = 'docs/dict-conjugated.json.gz';
  const NEO_PATH = '/nhe-enga/neologisms.csv';

  const MODES = ['indicativo', 'permissivo', 'circunstancial', 'gerundio', 'imperativo', 'conjuntivo'];
  const TUPI_START_RE = /^[\p{L}\p{M}'’]/u;
  const TUPI_DIALOGUE_RE = /^-[\p{L}\p{M}'’]/u;
  const TUPI_DIALOGUE_LEAD_RE = /^-\s*/;
  const TUPI_LETTER_RE = /[\p{L}\p{M}'’]/u;
  const TUPI_HEAD_CHAR_RE = /[\p{L}\p{M}'’?!-]/u;

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

  function normalizeApostrophes(str) {
    return str.replace(/[\u2018\u2019\u201B\u02BB\u02BC\uFF07]/g, "'");
  }

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
    return removePunctuation(normalizeApostrophes(str)).toLowerCase();
  }

  function normalizeNoAccent(str) {
    return removeDiacritics(str).toLowerCase();
  }

  function buildSearchIndex(data) {
    return data.map((item) => {
      item.first_word = normalizeApostrophes(item.first_word || '');
      item.definition = normalizeApostrophes(item.definition || '');
      if (typeof item.con === 'string') {
        item.con = normalizeApostrophes(item.con);
      }

      return {
        item,
        firstWordExact: normalizeExact(item.first_word),
        firstWordNoAccent: normalizeNoAccent(item.first_word),
        definitionLower: item.definition.toLowerCase(),
        definitionNoAccent: normalizeNoAccent(item.definition),
      };
    });
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

    // Navarro cites the 1929 Portuguese edition. Its printed page number is
    // also the zero-based scan filename; the PDF's page ordinal is one higher.
    // Keep each page in lists/ranges clickable without changing citation text.
    let regex = /\b(D['’‘ʼ]\s*[EÉÈÊ]vreux,\s*Viagem,\s*(?:pp?\.\s*)?)(\d+(?:\s*[-–—,]\s*\d+)*)(?![\dA-Za-zÀ-ÿ])/gi;
    replacedString = replacedString.replace(regex, (match, prefix, pages) => {
      const pageNumbers = pages.match(/\d+/g).map(Number);
      if (pageNumbers.some((page) => page < 14 || page > 442)) {
        return match;
      }
      let firstPage = true;
      return pages.replace(/\d+/g, (page) => {
        const label = firstPage ? `${prefix}${page}` : page;
        firstPage = false;
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=evreux1929&page_number=${Number(page)}" target="_blank" rel="noopener">${label}</a>`;
      });
    });

    // Navarro's lone "1686" Figueira citation is a probable year typo. The
    // catalogued 1687 edition (in Platzmann's 1878 facsimile) has the exact
    // cited çoába passage on p. 64. Preserve the year and let the viewer
    // explain the discrepancy.
    regex = /\b(Fig\.,?\s*Arte,\s*1686,\s*)(64)(?![\dA-Za-zÀ-ÿ])/g;
    replacedString = replacedString.replace(regex, (match) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=figueira1878&page_number=64&citation_year=1686" target="_blank" rel="noopener">${match}</a>`
    ));

    // Figueira's 1687 pagination is preserved by the 1878 facsimile. Keep
    // each page in inherited lists/ranges clickable without changing text.
    regex = /\b(Fig\.,?\s*Arte,\s*(?!1686\s*,)(?:pp?\.\s*)?)(\d+(?:\s*[-–—,;]\s*\d+)*)(?![\dA-Za-zÀ-ÿ])/g;
    replacedString = replacedString.replace(regex, (match, prefix, pages) => {
      const pageNumbers = pages.match(/\d+/g).map(Number);
      if (pageNumbers.some((page) => page < 1 || page > 167)) return match;
      let firstPage = true;
      return pages.replace(/\d+/g, (page) => {
        const label = firstPage ? `${prefix}${page}` : page;
        firstPage = false;
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=figueira1878&page_number=${Number(page)}" target="_blank" rel="noopener">${label}</a>`;
      });
    });

    // Castilho is intentionally a sparse set of verified cited-page crops.
    // The viewer manifest supplies the non-linear spread/side mapping.
    regex = /\b(Castilho,\s*Nomes,\s*(?:pp?\.\s*)?)(\d+(?:\s*[-–—,;]\s*\d+)*)(?![\dA-Za-zÀ-ÿ])/g;
    replacedString = replacedString.replace(regex, (match, prefix, pages) => {
      const availablePages = new Set([27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 45]);
      const pageNumbers = pages.match(/\d+/g).map(Number);
      if (pageNumbers.some((page) => !availablePages.has(page))) return match;
      let firstPage = true;
      return pages.replace(/\d+/g, (page) => {
        const label = firstPage ? `${prefix}${page}` : page;
        firstPage = false;
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=castilho1937&page_number=${Number(page)}" target="_blank" rel="noopener">${label}</a>`;
      });
    });

    // The cited Navarro page and the available Martins documentary edition
    // have no general numeric offset. Page 176 is linked only because all nine
    // unsuffixed quotations on that locator were explicitly aligned to
    // Martins 1954, p. 632. The separately cited 2006 edition stays unlinked.
    regex = /\bAnch\.,\s*Teatro,\s*176(?=\s*(?:\)|$))/g;
    replacedString = replacedString.replace(regex, (match) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=anchteatro1954&page_number=176" target="_blank" rel="noopener">${match}</a>`
    ));

    // VLB
    regex = /VLB, (I|II), (\d+)/g;
    replacedString = replacedString.replace(regex, (match, p1, p2) => {
      if (p1 === 'II') {
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=vlb&page_number=${parseInt(p2, 10) + 154}" target="_blank" rel="noopener">${match}</a>`;
      }
      return `<a href="/nhe-enga/docs/primary_sources/?book_name=vlb&page_number=${p2}" target="_blank" rel="noopener">${match}</a>`;
    });

    // Anchieta Arte
    regex = /Anch\., Arte, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, p1) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=ancharte&page_number=${p1}" target="_blank" rel="noopener">${match}</a>`
    ));

    // Araújo, Catecismo. An explicit 1686 suffix selects the second edition;
    // citations without an edition retain the historic 1618 behavior.
    regex = /Ar\., Cat\., (\d+(?:\s*[-–—]\s*\d+)?),\s*1686\b|Ar\., Cat\., (?!1686\b)(\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, pages1686, page1618) => {
      if (!pages1686) {
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=arcat1618&page_number=${page1618}" target="_blank" rel="noopener">${match}</a>`;
      }
      let firstPage = true;
      return pages1686.replace(/\d+/g, (page) => {
        const label = firstPage ? `Ar., Cat., ${page}` : page;
        firstPage = false;
        return `<a href="/nhe-enga/docs/primary_sources/?book_name=arcat1686&page_number=${Number(page)}" target="_blank" rel="noopener">${label}</a>`;
      }) + ', 1686';
    });

    // Bettendorf compendio
    regex = /Bettendorff, Compêndio, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, p1) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=betcomp&page_number=${Number(p1) + 9}" target="_blank" rel="noopener">${match}</a>`
    ));

    // Lery Histoire
    regex = /L(é|e)ry, Histoire, (\d+v?)/g;
    replacedString = replacedString.replace(regex, (match, _p1, p2) => (
      `<a href="/nhe-enga/docs/primary_sources/?book_name=lerhist&page_number=${Number(p2) + (341 - 287)}" target="_blank" rel="noopener">${match}</a>`
    ));

    return replacedString;
  }

  function splitByBullet(text) {
    const parts = [];
    let current = '';
    let parenDepth = 0;
    let bracketDepth = 0;

    for (let idx = 0; idx < text.length; idx += 1) {
      const ch = text[idx];
      if (ch === '(') {
        parenDepth += 1;
      } else if (ch === ')' && parenDepth > 0) {
        parenDepth -= 1;
      } else if (ch === '[') {
        bracketDepth += 1;
      } else if (ch === ']' && bracketDepth > 0) {
        bracketDepth -= 1;
      }

      if (ch === '●' && parenDepth === 0 && bracketDepth === 0) {
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
    let bracketDepth = 0;
    const upper = text.toUpperCase();
    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      if (char === '(') {
        parenDepth += 1;
      } else if (char === ')' && parenDepth > 0) {
        parenDepth -= 1;
      } else if (char === '[') {
        bracketDepth += 1;
      } else if (char === ']' && bracketDepth > 0) {
        bracketDepth -= 1;
      }

      if (parenDepth === 0 && bracketDepth === 0 && upper.startsWith('NOTA', i)) {
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
    let bracketDepth = 0;
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
      } else if (char === '[') {
        bracketDepth += 1;
      } else if (char === ']' && bracketDepth > 0) {
        bracketDepth -= 1;
      }

      if (parenDepth === 0 && bracketDepth === 0 && atEntryStart) {
        let j = i;
        while (j < len && /\s/.test(section[j])) {
          j += 1;
        }

        const startsWithMorphologicalHyphen = section[j] === '-'
          && isLetterStart(section[j + 1]);
        if (
          j < len
          && (isLetterStart(section[j]) || startsWithMorphologicalHyphen)
        ) {
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

      if (parenDepth === 0 && bracketDepth === 0 && (char === ';' || char === '●')) {
        atEntryStart = true;
      } else if (!/\s/.test(char)) {
        atEntryStart = false;
      }

      i += 1;
    }

    return output;
  }

  function formatVerbeteSection(section, allowInitialDefinition = true) {
    let output = '';
    let i = 0;
    let parenDepth = 0;
    let bracketDepth = 0;
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
    const balanceLabelMetadata = (metadata) => {
      const trimmed = (metadata || '').trim();
      const opens = (trimmed.match(/\(/g) || []).length;
      const closes = (trimmed.match(/\)/g) || []).length;
      return opens === closes + 1 ? `${trimmed})` : trimmed;
    };
    const matchSectionLabel = (value) => {
      // Recover the occasional source typo that opens a parenthetical
      // adjective/adverb label but closes it with `]`.
      const bracketClosedParenthetical = value.match(
        /^\(\s*(adj|adv)\.?\s*(?::|-)\s*([^\]]+)\]\s*(\([^)]*\)\s*)?-\s*/i
      );
      if (bracketClosedParenthetical) {
        return {
          length: bracketClosedParenthetical[0].length,
          key: `${bracketClosedParenthetical[1].toLowerCase()}.`,
          metadata: balanceLabelMetadata(bracketClosedParenthetical[2]),
          definitionPrefix: (bracketClosedParenthetical[3] || '').trim(),
        };
      }

      const parenthetical = value.match(
        /^\(\s*(adj|adv)\.?\s*(?:(?::|-)\s*([^)]+))?\)\s*(\([^)]*\)\s*)?(?:([:–—-])\s*)?/i
      );
      if (parenthetical) {
        return {
          length: parenthetical[0].length,
          key: `${parenthetical[1].toLowerCase()}.`,
          metadata: balanceLabelMetadata(parenthetical[2]),
          definitionPrefix: (parenthetical[3] || '').trim(),
        };
      }

      const bracketed = value.match(
        /^\[\s*(adj|adv)\.?\s*(?::|-)\s*([^\]]+)\]\s*;?\s*(\([^)]*\)\s*)?-\s*/i
      );
      if (!bracketed) return null;
      return {
        length: bracketed[0].length,
        key: `${bracketed[1].toLowerCase()}.`,
        metadata: balanceLabelMetadata(bracketed[2]),
        definitionPrefix: (bracketed[3] || '').trim(),
      };
    };
    const matchDefinitionLabel = (value) => {
      if (!allowInitialDefinition) return null;
      const matchAnnotatedPrefix = () => {
        if (i !== 0) return null;
        const start = value.search(/\S/);
        if (start === -1 || !/[([/]/.test(value[start])) return null;

        let localParenDepth = 0;
        let localBracketDepth = 0;
        for (let idx = start; idx < value.length; idx += 1) {
          const ch = value[idx];
          if (ch === '(') {
            localParenDepth += 1;
            continue;
          }
          if (ch === ')' && localParenDepth > 0) {
            localParenDepth -= 1;
            continue;
          }
          if (ch === ')' && localBracketDepth > 0) {
            // A handful of source labels open with `[` but close with `)`.
            // Treat that mismatched closer as the end of the annotation so
            // the following gloss can still receive definition styling.
            localBracketDepth -= 1;
            continue;
          }
          if (ch === '[') {
            localBracketDepth += 1;
            continue;
          }
          if (ch === ']' && localBracketDepth > 0) {
            localBracketDepth -= 1;
            continue;
          }
          if (localParenDepth !== 0 || localBracketDepth !== 0) continue;

          if (
            /^\d+\)/.test(value.slice(idx))
            && (idx === start || /\s/.test(value[idx - 1] || ''))
          ) {
            // This is a numbered entry whose first sense happens to begin
            // with an annotation, not one unnumbered annotated gloss.  Let
            // the regular numbered-sense parser retain the `1)` boundary.
            return null;
          }

          const isColon = ch === ':';
          const isDash = /[-–—]/.test(ch)
            && /\s/.test(value[idx - 1] || '')
            && /\s/.test(value[idx + 1] || '');
          if (!isColon && !isDash) continue;

          const prefix = value.slice(start, idx).trim();
          if (!/[)\]]/.test(prefix)) return null;
          if (/\((?:adj|adv)\.\)\s*$/i.test(prefix)) {
            // Leave bare section labels to matchSectionLabel so they retain
            // their visible `Adjetivo:` / `Advérbio:` headings.
            return null;
          }
          let end = idx + 1;
          while (end < value.length && /\s/.test(value[end])) end += 1;

          let tailParenDepth = 0;
          let tailBracketDepth = 0;
          let glossColonFound = false;
          for (let tailIndex = end; tailIndex < value.length; tailIndex += 1) {
            const tailChar = value[tailIndex];
            if (tailChar === '(') {
              tailParenDepth += 1;
              continue;
            }
            if (tailChar === ')' && tailParenDepth > 0) {
              tailParenDepth -= 1;
              continue;
            }
            if (tailChar === '[') {
              tailBracketDepth += 1;
              continue;
            }
            if (tailChar === ']' && tailBracketDepth > 0) {
              tailBracketDepth -= 1;
              continue;
            }
            if (tailParenDepth !== 0 || tailBracketDepth !== 0) continue;
            if (tailChar === ':') {
              glossColonFound = true;
              break;
            }
            if (
              /[-–—]/.test(tailChar)
              && /\s/.test(value[tailIndex - 1] || '')
              && /\s/.test(value[tailIndex + 1] || '')
            ) {
              break;
            }
          }
          if (!glossColonFound) return null;

          const match = [value.slice(0, end), isColon ? ':' : '-'];
          match.requiresGlossColon = true;
          return match;
        }
        return null;
      };

      const grammaticalLabel = value.match(
        /^(?:\(\s*(?:(?:s|v)\.[^)]*|(?:s|v)(?=\s*\))|(?:dem\.\s*)?pron\.[^)]*|part\.[^)]*|conj\.[^)]*|interj\.[^)]*|interr\.[^)]*|(?:loc\.\s*)?posp\.[^)]*|num\.[^)]*|suf\.[^)]*|pref\.[^)]*)\)|\[\s*(?:(?:s|v)\.[^)]*|(?:s|v)(?=\s*\))|(?:dem\.\s*)?pron\.[^)]*|part\.[^)]*|conj\.[^)]*|interj\.[^)]*|interr\.[^)]*|(?:loc\.\s*)?posp\.[^)]*|num\.[^)]*|suf\.[^)]*|pref\.[^)]*)\))/i
      );
      if (!grammaticalLabel) return matchAnnotatedPrefix();
      if (grammaticalLabel[0].startsWith('[') && value.includes(']')) {
        // Do not mistake a parenthesis inside a well-formed bracketed label
        // for the label's closer.  The `[` ... `)` branch exists only to
        // recover genuinely mismatched source labels with no closing bracket.
        return matchAnnotatedPrefix();
      }

      let cursor = grammaticalLabel[0].length;
      while (cursor < value.length) {
        let metadataStart = cursor;
        while (metadataStart < value.length && /\s/.test(value[metadataStart])) {
          metadataStart += 1;
        }
        if (value[metadataStart] !== '(') {
          cursor = metadataStart;
          break;
        }

        let depth = 0;
        let metadataEnd = metadataStart;
        for (; metadataEnd < value.length; metadataEnd += 1) {
          if (value[metadataEnd] === '(') depth += 1;
          if (value[metadataEnd] === ')') {
            depth -= 1;
            if (depth === 0) {
              metadataEnd += 1;
              break;
            }
          }
        }
        if (depth !== 0) return null;
        cursor = metadataEnd;
      }

      const delimiter = value.slice(cursor).match(/^(-|:)\s*/);
      if (!delimiter) {
        // One conjunction entry omits the conventional separator after its
        // grammatical label.  Let the normal top-level-colon check below
        // decide whether the following lowercase text is a gloss; source
        // examples with no such colon remain definitionless.
        if (!/^[a-zà-ÿ]/.test(value.slice(cursor))) {
          return matchAnnotatedPrefix();
        }
        return [value.slice(0, cursor), ':'];
      }
      const fullText = value.slice(0, cursor + delimiter[0].length);
      // Preserve the array-shaped contract used below: [0] is the complete
      // source label and [1] is the definition delimiter.
      return [fullText, delimiter[1]];
    };
    const isBareSectionLabel = (value) => (
      /^(?:\[\s*(?:adj|adv)\.?\s*(?::|-)[^\]]+\]|\(\s*(?:adj|adv)\.?\s*(?::|-)[^)\]]+[)\]])\s*$/i
        .test(value.trim())
    );
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
    const RAW_SOURCE_LOCATOR_TAIL_RE = /(?:^|[,;]\s*)(?:(?:(?:p\.\s*)?\d+(?:[vr])?|[IVXLCDM]+|cap\.\s*[IVXLCDMivxlcdm]+|§\s*\d+[a-z]?)(?:\s*[-–]\s*(?:\d+(?:[vr])?|[IVXLCDM]+))?(?:\s*,\s*\d{4})?(?:\s*[,;]\s*adapt\.)?|(?:in\s+)?Ar\.,\s*Cat)\]?\s*\.?$/;
    const hasRawTrailingSourceCitation = (value) => {
      const citationMatch = value.trim().match(/(\([^()]+\))\s*\.?$/);
      if (!citationMatch) return false;
      const inner = citationMatch[1].slice(1, -1).trim();
      return inner.includes(',') && RAW_SOURCE_LOCATOR_TAIL_RE.test(inner);
    };
    const nextTopLevelChunk = (startIndex) => {
      let lookaheadParenDepth = 0;
      let lookaheadBracketDepth = 0;
      let endIndex = section.length;

      for (let idx = startIndex; idx < section.length; idx += 1) {
        const ch = section[idx];
        if (ch === '(') {
          lookaheadParenDepth += 1;
          continue;
        }
        if (ch === ')' && lookaheadParenDepth > 0) {
          lookaheadParenDepth -= 1;
          continue;
        }
        if (ch === '[') {
          lookaheadBracketDepth += 1;
          continue;
        }
        if (ch === ']' && lookaheadBracketDepth > 0) {
          lookaheadBracketDepth -= 1;
          continue;
        }
        if (
          lookaheadParenDepth === 0
          && lookaheadBracketDepth === 0
          && (ch === ';' || ch === '●')
        ) {
          endIndex = idx;
          break;
        }
      }
      return section.slice(startIndex, endIndex).trim();
    };
    const countTopLevelTranslationDashes = (value) => {
      let dashCount = 0;
      let lookaheadParenDepth = 0;
      let lookaheadBracketDepth = 0;

      for (let idx = 0; idx < value.length; idx += 1) {
        const ch = value[idx];
        if (ch === '(') {
          lookaheadParenDepth += 1;
          continue;
        }
        if (ch === ')' && lookaheadParenDepth > 0) {
          lookaheadParenDepth -= 1;
          continue;
        }
        if (ch === '[') {
          lookaheadBracketDepth += 1;
          continue;
        }
        if (ch === ']' && lookaheadBracketDepth > 0) {
          lookaheadBracketDepth -= 1;
          continue;
        }
        if (
          ch === '-'
          && lookaheadParenDepth === 0
          && lookaheadBracketDepth === 0
          && /[\s.!?…]/.test(value[idx - 1] || '')
          && /\s/.test(value[idx + 1] || '')
        ) {
          dashCount += 1;
        }
      }
      return dashCount;
    };
    const nextRawCitedTail = (startIndex) => {
      let lookaheadParenDepth = 0;
      let lookaheadBracketDepth = 0;

      for (let idx = startIndex; idx < section.length; idx += 1) {
        const ch = section[idx];
        if (ch === '(') {
          lookaheadParenDepth += 1;
        } else if (ch === ')' && lookaheadParenDepth > 0) {
          lookaheadParenDepth -= 1;
          if (
            lookaheadParenDepth === 0
            && lookaheadBracketDepth === 0
          ) {
            const candidate = section.slice(startIndex, idx + 1);
            if (hasRawTrailingSourceCitation(candidate)) return candidate;
          }
        } else if (ch === '[') {
          lookaheadBracketDepth += 1;
        } else if (ch === ']' && lookaheadBracketDepth > 0) {
          lookaheadBracketDepth -= 1;
        } else if (ch === ']' && lookaheadParenDepth > 0) {
          lookaheadParenDepth -= 1;
        } else if (
          ch === '●'
          && lookaheadParenDepth === 0
          && lookaheadBracketDepth === 0
        ) {
          break;
        }
      }
      return '';
    };
    const semicolonContinuesSingleCitedPair = (startIndex) => {
      if (definitionOpen || hasRawTrailingSourceCitation(output)) return false;
      const citedTail = nextRawCitedTail(startIndex);
      if (!citedTail) return false;

      const combined = `${output};${citedTail}`;
      const lastDefinitionClose = combined.lastIndexOf('</span>');
      const quotePortion = lastDefinitionClose === -1
        ? combined
        : combined.slice(lastDefinitionClose + '</span>'.length);
      return countTopLevelTranslationDashes(quotePortion) === 1;
    };
    const semicolonContinuesPortugueseTranslation = (startIndex) => {
      if (definitionOpen || hasRawTrailingSourceCitation(output)) return false;
      const lastDefinitionClose = output.lastIndexOf('</span>');
      const quotePortion = lastDefinitionClose === -1
        ? output
        : output.slice(lastDefinitionClose + '</span>'.length);
      if (countTopLevelTranslationDashes(quotePortion) !== 1) return false;

      const continuation = nextTopLevelChunk(startIndex)
        .replace(/<\/?[A-Za-z][^>]*>/g, '')
        .trim();
      if (
        !continuation
        || countTopLevelTranslationDashes(continuation) > 0
        || hasRawTrailingSourceCitation(continuation)
      ) {
        return false;
      }
      return /^[a-zà-ÿ]/.test(continuation)
        && /\b(?:de|da|do|das|dos|na|no|nas|nos|meu|minha|seu|sua|dele|dela|é|são)\b/i.test(continuation)
        && !/(?:[îûŷãẽĩõũ]|gû|kû|[aeiouáéíóú]['’])/i.test(continuation);
    };
    const firstTopLevelColon = (value) => {
      let lookaheadParenDepth = 0;
      let lookaheadBracketDepth = 0;
      for (let idx = 0; idx < value.length; idx += 1) {
        const ch = value[idx];
        if (ch === '(') {
          lookaheadParenDepth += 1;
        } else if (ch === ')' && lookaheadParenDepth > 0) {
          lookaheadParenDepth -= 1;
        } else if (ch === '[') {
          lookaheadBracketDepth += 1;
        } else if (ch === ']' && lookaheadBracketDepth > 0) {
          lookaheadBracketDepth -= 1;
        } else if (
          ch === ':'
          && lookaheadParenDepth === 0
          && lookaheadBracketDepth === 0
        ) {
          return idx;
        }
      }
      return -1;
    };
    const definitionContinuesAfterSemicolon = (startIndex) => {
      const chunk = nextTopLevelChunk(startIndex);
      if (!chunk) return false;
      if (/^(?:\d+|[a-z])\)/i.test(chunk)) return false;
      if (matchSectionLabel(chunk)) return false;
      if (isBareSectionLabel(chunk)) return false;
      if (/^\([^)]{1,24}\)\s*-\s+/.test(chunk)) return true;

      const dashCount = countTopLevelTranslationDashes(chunk);
      const colonIndex = firstTopLevelColon(chunk);
      if (colonIndex !== -1) {
        const prefix = chunk.slice(0, colonIndex);
        if (countTopLevelTranslationDashes(prefix) === 0) return true;
      }
      if (hasRawTrailingSourceCitation(chunk) && dashCount === 1) return false;
      if (
        hasRawTrailingSourceCitation(chunk)
        && /^-\s*[A-Za-zÀ-ÿ\u0176\u0177'’]/.test(chunk)
      ) {
        return false;
      }
      return true;
    };
    const segments = [];

    while (i < section.length) {
      const char = section[i];
      const plainOutputBeforeChar = output.replace(/<\/?[A-Za-z][^>]*>/g, '').trim();
      const looksLikeCompactTranslation = char === '-'
        && !definitionOpen
        && /[.!?…][\"'’”]?$/.test(plainOutputBeforeChar)
        && /[A-ZÀ-ÖØ-ÞŶ]/.test(section[i + 1] || '');

      if (parenDepth === 0 && bracketDepth === 0) {
        const labelMatch = matchSectionLabel(section.slice(i));
        if (labelMatch) {
          if (definitionOpen) {
            const emptyDefinition = output.match(/<span class="sense-definition">\s*$/i);
            if (emptyDefinition) {
              output = output.slice(0, -emptyDefinition[0].length);
            } else {
              output += '</span>';
            }
            definitionOpen = false;
          }
          let lookahead = i + labelMatch.length;
          while (lookahead < section.length && /\s/.test(section[lookahead])) {
            lookahead += 1;
          }
          const hasNumberAhead = /^\d+\)/.test(section.slice(lookahead));
          const startsDialogueAhead = /^-\s*[A-Za-zÀ-ÿ\u0176\u0177'’]/.test(
            section.slice(lookahead)
          );

          if (output.length && !output.endsWith('<br>')) {
            output += '<br>';
          }
          if (sectionLabelMap[labelMatch.key]) {
            const metadata = labelMatch.metadata ? ` ${labelMatch.metadata}` : '';
            output += `<div class="sense-section-title">${sectionLabelMap[labelMatch.key]}:${metadata}</div>`;
          }
          if (hasNumberAhead) {
            expectedNumber = 1;
            expectedLetter = 'a';
            seenNumber = false;
          }
          if (!hasNumberAhead && !startsDialogueAhead) {
            output += '<span class="sense-definition">';
            if (labelMatch.definitionPrefix) {
              output += `${labelMatch.definitionPrefix} `;
            }
            definitionOpen = true;
            if (!seenNumber) {
              expectedNumber = 1;
              expectedLetter = 'a';
            }
          }
          i += labelMatch.length;
          continue;
        }

        const definitionLabelMatch = !definitionOpen
          ? matchDefinitionLabel(section.slice(i))
          : null;
        if (definitionLabelMatch) {
          let lookahead = i + definitionLabelMatch[0].length;
          while (lookahead < section.length && /\s/.test(section[lookahead])) {
            lookahead += 1;
          }
          const hasNumberAhead = /^\d+\)/.test(section.slice(lookahead))
            || /(?:^|\s)1\)/.test(nextTopLevelChunk(lookahead));
          const hasImplicitFirstSense = !hasNumberAhead
            && /;\s*2\)/.test(section.slice(lookahead));
          const startsDialogueAhead = /^-\s*[A-Za-zÀ-ÿ\u0176\u0177'’]/.test(
            section.slice(lookahead)
          );
          const remaining = section.slice(lookahead);
          const nextColon = firstTopLevelColon(remaining);
          const hasGlossColon = nextColon !== -1
            && countTopLevelTranslationDashes(remaining.slice(0, nextColon)) === 0;
          const colonIntroducesGloss = definitionLabelMatch[1] === ':'
            && hasGlossColon;
          const dashIntroducesGloss = definitionLabelMatch[1] === '-'
            && (
              !definitionLabelMatch.requiresGlossColon
              || hasGlossColon
            );
          output += definitionLabelMatch[0];
          if (
            !hasNumberAhead
            && !startsDialogueAhead
            && (dashIntroducesGloss || colonIntroducesGloss)
          ) {
            output += '<span class="sense-definition">';
            definitionOpen = true;
            if (hasImplicitFirstSense) {
              expectedNumber = 2;
              expectedLetter = 'a';
              seenNumber = true;
            }
          }
          i += definitionLabelMatch[0].length;
          continue;
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
              const separatorMatch = section
                .slice(i + numberMatch[0].length)
                .match(/^\s+[-–—]\s+/);
              if (separatorMatch) output += ' ';
              i += numberMatch[0].length + (separatorMatch ? separatorMatch[0].length : 0);
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
              const separatorMatch = section
                .slice(i + letterMatch[0].length)
                .match(/^\s+[-–—]\s+/);
              if (separatorMatch) output += ' ';
              i += letterMatch[0].length + (separatorMatch ? separatorMatch[0].length : 0);
              continue;
            }
          }
        }
      }

      if (
        parenDepth === 0 &&
        bracketDepth === 0 &&
        char === '-' &&
        TUPI_LETTER_RE.test(section[i + 1]) &&
        /\s/.test(section[i - 1] || '') &&
        (
          plainOutputBeforeChar === ''
          || /[:.!?…]["'’”)]?$/.test(plainOutputBeforeChar)
          || /<\/div>\s*$/i.test(output)
          || (definitionOpen && hasRawTrailingSourceCitation(output))
        ) &&
        !looksLikeCompactTranslation &&
        !(
          definitionOpen
          && /<span class="sense-definition">\s*$/i.test(output)
        )
      ) {
        if (!inDialogueSegment) {
          inDialogueSegment = true;
          if (definitionOpen) {
            output += '</span>';
            definitionOpen = false;
          }
          if (output.trim().length > 0) {
            segments.push(output);
            output = '';
            continue;
          }
        }
      }

      if (definitionOpen && parenDepth === 0 && bracketDepth === 0 && char === ':') {
        output += '</span>';
        definitionOpen = false;
        output += char;
        i += 1;
        continue;
      }

      if (char === ';' && parenDepth === 0 && bracketDepth === 0) {
        if (inDialogueSegment && !hasRawTrailingSourceCitation(output)) {
          output += char;
          i += 1;
          continue;
        }
        if (semicolonContinuesSingleCitedPair(i + 1)) {
          output += char;
          i += 1;
          continue;
        }
        if (semicolonContinuesPortugueseTranslation(i + 1)) {
          output += char;
          i += 1;
          continue;
        }
        if (definitionOpen && definitionContinuesAfterSemicolon(i + 1)) {
          output += char;
          i += 1;
          continue;
        }
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
      } else if (char === '[') {
        bracketDepth += 1;
      } else if (char === ']' && bracketDepth > 0) {
        bracketDepth -= 1;
      } else if (char === ']' && parenDepth > 0) {
        // A few source records close a parenthetical valency note with `]`.
        // Recover at the mismatched closer so the following example colon is
        // still treated as a top-level boundary.
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
    const quoteStartRe = /^(\"|“|”|'|‘|’|\.\.\.|…)/;
    const stripTags = (text) => text.replace(/<\/?[A-Za-z][^>]*>/g, '');
    const looksLikeTupiText = (text) => (
      /(?:[îûŷãẽĩõũ]|gû|kû|nh|mb|nd|[aeiouáéíóú]['’]|\b(?:xe|nde|oré|îandé|tupã)\b)/i.test(stripTags(text))
    );
    const looksDistinctivelyTupiText = (text) => (
      /(?:[îûŷẽĩũ]|gû|kû|[aeiouáéíóú]['’]|['’][aeiouáéíóú]|\b(?:xe|nde|oré|îandé|tupã)\b)/i.test(stripTags(text))
    );
    const looksLikePortugueseText = (text) => (
      /(?:^|[\s"“”([{])(?:a|as|o|os|um|uma|de|do|da|em|eu|tu|ele|ela|dele|dela|nós|vós|não|que|com|para|por|me|te|se|meu|minha|mas|estou|sou|será|são|eia|diante|disseste)(?=$|[\s.,;:!?…"“”)\]}])/iu.test(
        stripTags(text)
      )
    );
    const SOURCE_LOCATOR_TAIL_RE = /(?:^|[,;]\s*)(?:(?:(?:p\.\s*)?\d+(?:[vr])?|[IVXLCDM]+|cap\.\s*[IVXLCDMivxlcdm]+|§\s*\d+[a-z]?)(?:\s*[-–]\s*(?:\d+(?:[vr])?|[IVXLCDM]+))?(?:\s*,\s*\d{4})?(?:\s*[,;]\s*adapt\.)?|(?:in\s+)?Ar\.,\s*Cat)\]?\s*\.?$/;
    const isSourceCitation = (text) => {
      const plain = stripTags(text).trim();
      if (!/^\([^()]+\)$/.test(plain)) return false;
      const inner = plain.slice(1, -1).trim();
      return inner.includes(',') && SOURCE_LOCATOR_TAIL_RE.test(inner);
    };

    const extractTrailingCitation = (text) => {
      const trimmed = normalizeQuoteText(text);
      if (!trimmed.endsWith(')')) {
        return { body: trimmed, citation: '' };
      }

      let cursor = trimmed.length;
      let citationStart = trimmed.length;
      const citations = [];

      while (cursor > 0) {
        while (cursor > 0 && /\s/.test(trimmed[cursor - 1])) cursor -= 1;
        if (trimmed[cursor - 1] !== ')') break;

        let depth = 0;
        let start = -1;
        for (let idx = cursor - 1; idx >= 0; idx -= 1) {
          if (trimmed[idx] === ')') depth += 1;
          if (trimmed[idx] !== '(') continue;
          depth -= 1;
          if (depth === 0) {
            start = idx;
            break;
          }
        }

        if (start === -1) break;
        const candidate = trimmed.slice(start, cursor).trim();
        if (!isSourceCitation(candidate)) break;
        citations.unshift(candidate);
        citationStart = start;
        cursor = start;
      }

      if (!citations.length) return { body: trimmed, citation: '' };
      return {
        body: trimmed.slice(0, citationStart).trim(),
        citation: citations.join(' '),
      };
    };

    const findTranslationSeparators = (text) => {
      const normalized = normalizeQuoteText(text);
      const isTopLevelAt = (value, targetIndex) => {
        let parenDepth = 0;
        let bracketDepth = 0;
        for (let idx = 0; idx < targetIndex; idx += 1) {
          if (value[idx] === '<') {
            const tagMatch = value.slice(idx).match(/^<\/?[A-Za-z][^>]*>/);
            if (tagMatch) {
              idx += tagMatch[0].length - 1;
              continue;
            }
          }
          if (value[idx] === '(') parenDepth += 1;
          if (value[idx] === ')' && parenDepth > 0) parenDepth -= 1;
          else if (value[idx] === ')' && bracketDepth > 0) bracketDepth -= 1;
          if (value[idx] === '[') bracketDepth += 1;
          if (value[idx] === ']' && bracketDepth > 0) bracketDepth -= 1;
          else if (value[idx] === ']' && parenDepth > 0) parenDepth -= 1;
        }
        return parenDepth === 0 && bracketDepth === 0;
      };
      const isCategoryPrefix = (prefix) => (
        /^\s*(?:\[\s*(?:adj|adv|s|v)\.?\s*(?::|-)[^\]]+\]|\(\s*(?:adj|adv|s|v)\.?[^)]*\))(?:\s*\([^)]*\))*\s*$/i.test(stripTags(prefix))
      );
      const ordinary = [...normalized.matchAll(/(?:\s|[.!?…])-\s+/g)]
        .map((match) => {
          const punctuationAdjacent = /[.!?…]/.test(match[0][0]);
          return {
            index: match.index + (punctuationAdjacent ? 1 : 0),
            length: match[0].length - (punctuationAdjacent ? 1 : 0),
            compact: false,
          };
        })
        .filter((separator) => (
          isTopLevelAt(normalized, separator.index)
          && !isCategoryPrefix(normalized.slice(0, separator.index))
        ));
      if (ordinary.length) return ordinary;

      // A handful of source dialogues omit the space after both turn dashes
      // ("-Tupi. -Portuguese.").  Requiring that exact, cited shape avoids
      // treating productive suffix notation such as "-usu" as a translation.
      const { body, citation } = extractTrailingCitation(normalized);
      if (!citation) return [];

      // Recover citation-backed translations whose dash directly touches the
      // Portuguese text after source-sentence punctuation.
      const punctuationCompact = [...body.matchAll(/[.!?…]\s*-(?=(?:["“”]\s*)?[A-ZÀ-ÖØ-ÞŶ])/g)]
        .filter((match) => isTopLevelAt(body, match.index))
        .map((match) => ({
          index: match.index + match[0].lastIndexOf('-'),
          length: 1,
          compact: true,
        }));
      if (punctuationCompact.length) return [punctuationCompact[0]];

      const compactTurnStart = /^(?:[\"“”]\s*)?-[A-Za-zÀ-ÿ\u0176\u0177'’]/;
      if (!compactTurnStart.test(body.trim())) return [];
      const compact = [...body.matchAll(/\s-(?=\S)/g)]
        .filter((match) => isTopLevelAt(body, match.index))
        .map((match) => ({
          index: match.index,
          length: match[0].length,
          compact: true,
        }));
      return compact.length ? [compact[0]] : [];
    };

    const countDash = (text) => findTranslationSeparators(text).length;
    const hasDash = (text) => countDash(text) > 0;
    const hasCitation = (text) => (
      (normalizeQuoteText(text).match(/\([^()]*\)/g) || []).some(isSourceCitation)
    );
    const hasTrailingCitation = (text) => Boolean(extractTrailingCitation(text).citation);

    const splitQuoteLines = (text) => {
      const { body, citation } = extractTrailingCitation(text);
      const separators = findTranslationSeparators(text);
      if (!separators.length) {
        const trimmedBody = body.trim();
        if (quoteStartRe.test(trimmedBody)) {
          return { tupi: '', pt: body, citation };
        }
        return { tupi: body, pt: '', citation };
      }

      const separator = separators[0];

      return {
        tupi: body.slice(0, separator.index).trim(),
        pt: body.slice(separator.index + separator.length).trim(),
        citation,
      };
    };

    const splitCompoundCitedPair = (text) => {
      const { body, citation } = extractTrailingCitation(text);
      if (!citation) return null;
      const separators = findTranslationSeparators(body);
      if (separators.length !== 2 && separators.length !== 3) return null;

      const parts = [];
      let cursor = 0;
      separators.forEach((separator) => {
        parts.push(body.slice(cursor, separator.index).trim());
        cursor = separator.index + separator.length;
      });
      parts.push(body.slice(cursor).trim());

      if (
        parts.length === 3
        && /^(?:\.{3}|…)$/u.test(stripTags(parts[0]))
        && looksLikeTupiText(parts[1])
        && looksLikePortugueseText(parts[2])
      ) {
        return { tupi: parts[1], pt: parts[2], citation };
      }

      if (
        parts.length === 3
        && parts.slice(0, 2).every(looksLikeTupiText)
        && looksDistinctivelyTupiText(parts[1])
        && !looksLikePortugueseText(parts[1])
        && looksLikePortugueseText(parts[2])
      ) {
        return {
          tupi: parts.slice(0, 2).join(' - '),
          pt: parts[2],
          citation,
        };
      }

      const midpoint = parts.length / 2;
      const alignedCompound = Number.isInteger(midpoint)
        && parts.slice(0, midpoint).every(looksDistinctivelyTupiText)
        && parts.slice(midpoint).every((part) => !looksDistinctivelyTupiText(part))
        && parts.slice(midpoint).some(looksLikePortugueseText);
      if (
        Number.isInteger(midpoint)
        && (
          (
            parts.slice(0, midpoint).every(looksLikeTupiText)
            && parts.slice(midpoint).every(looksLikePortugueseText)
          )
          || alignedCompound
        )
      ) {
        return {
          tupi: parts.slice(0, midpoint).join(' - '),
          pt: parts.slice(midpoint).join(' - '),
          citation,
        };
      }
      return null;
    };

    const splitDialogueSegments = (text) => {
      const segments = [];
      let start = -1;
      const len = text.length;

      for (let idx = 0; idx < len; idx += 1) {
        const char = text[idx];
        const prevChar = text[idx - 1];
        const previousNonSpace = text.slice(0, idx).match(/\S(?=\s*$)/)?.[0] || '';
        const isDialogueStart = char === '-'
          && /^-\s*(?:\.{3}|…)?\s*(?:\([^)]{1,12}\)\s*)?[A-Za-zÀ-ÿ\u0176\u0177'’]/.test(text.slice(idx))
          && (idx === 0 || /\s/.test(prevChar) || /[.!?…]/.test(prevChar))
          // A dash immediately after a colon commonly opens a quotation
          // inside a translated turn ("Dizem: -Meu compadre"), rather than a
          // new aligned dialogue row.
          && !(start !== -1 && previousNonSpace === ':');
        if (isDialogueStart) {
          if (start === -1) {
            const prefix = text
              .slice(0, idx)
              .replace(/^(?:\.{3}|…)\s*/, '')
              .trim();
            if (prefix) segments.push(prefix);
          } else {
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

      return segments.map((segment) => segment.replace(TUPI_DIALOGUE_LEAD_RE, '').trim()).filter(Boolean);
    };

    const parseDialogue = (text) => {
      const normalized = normalizeQuoteText(text);
      const { body, citation } = extractTrailingCitation(normalized);
      const segments = splitDialogueSegments(body);
      if (segments.length < 4 || segments.length % 2 !== 0) {
        return null;
      }

      const midpoint = segments.length / 2;
      const tupiLines = segments.slice(0, midpoint);
      const startsLikePortugueseTurn = /^(?:dói|moro|sou|estou|somos|tenho|temos|não|que|quem|como|por que|para|dizem|são|eles|elas|eu|nós|vós|meu|minha)\b/i;
      if (!tupiLines.every((line) => (
        /[.!?…]["'’”]?$/.test(line.trim())
        && !startsLikePortugueseTurn.test(line.trim())
      ))) {
        return null;
      }
      return {
        tupiLines,
        ptLines: segments.slice(midpoint),
        citation,
      };
    };

    const splitImplicitCitedPair = (text) => {
      const { body, citation } = extractTrailingCitation(text);
      if (!citation || hasDash(body) || parseDialogue(body)) return null;

      const boundaryRe = /[.!?…][\"'’”]?\s+(?=[A-ZÀ-ÖØ-ÞŶ])/g;
      let boundary;
      while ((boundary = boundaryRe.exec(body)) !== null) {
        const source = body.slice(0, boundary.index + boundary[0].trimEnd().length).trim();
        const portuguese = body.slice(boundary.index + boundary[0].length).trim();
        const plainSource = stripTags(source);
        const plainPortuguese = stripTags(portuguese);
        const looksLikeSourceStart = /^(?:["'‘’“”]\s*)?(?:-|\.{3}|…|[A-ZÀ-ÖØ-ÞŶ])/.test(
          plainSource
        );
        const looksTupi = /(?:[îûŷẽõ]|gû|kû|nh|mb|nd|[aeiouáéíóú]['’]|-[a-zà-ÿ])/i.test(plainSource);
        const looksPortuguese = (
          /\b(?:a|as|o|os|um|uma|de|do|da|em|eu|tu|ele|ela|nós|vós|não|que|com|para|por|me|te|se|meu|minha|mas|estou|sou|será|eia|diante|disseste)\b/i.test(
            plainPortuguese
          )
          || /(?:^|\s)ó(?=\s|$)/i.test(plainPortuguese)
        );
        if (
          source
          && portuguese
          && looksLikeSourceStart
          && looksTupi
          && looksPortuguese
        ) {
          return {
            source,
            portuguese,
            quoteText: `${source} - ${portuguese} ${citation}`,
          };
        }
      }
      return null;
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

    const stripLeadingDashSpace = (value) => value.replace(/^\s*-\s*/, '');

    const buildQuoteBlock = (rawText) => {
      const text = rawText.replace(
        /<span class="related-entry-headword"><a\b[^>]*>([\s\S]*?)<\/a><\/span>/gi,
        '$1'
      );
      const dialogue = parseDialogue(text);
      if (dialogue) {
        return buildDialogueBlock(dialogue.tupiLines, dialogue.ptLines, dialogue.citation);
      }

      let { tupi, pt, citation } = splitCompoundCitedPair(text) || splitQuoteLines(text);
      tupi = stripLeadingDashSpace(tupi);
      pt = stripLeadingDashSpace(pt);
      let editorialTail = '';
      const editorialTailMatch = pt.match(
        /\s+(\((?:o\s+mesmo\s+que|v\.\s*tb\.)[^()]*\))\s*$/i
      );
      if (editorialTailMatch) {
        editorialTail = ` ${editorialTailMatch[1]}`;
        pt = pt.slice(0, editorialTailMatch.index).trimEnd();
      }
      const citationHtml = citation ? ` <span class="quote-citation">${citation}</span>` : '';
      const tupiLine = tupi ? `<div class="quote-tupi">${tupi}${!pt ? citationHtml : ''}</div>` : '';
      const ptLine = pt ? `<div class="quote-pt">${pt}${citationHtml}</div>` : '';
      const citationLine = !pt && !tupi && citation ? `<div class="quote-citation">${citation}</div>` : '';

      return `<div class="sense-quote">${tupiLine}${ptLine}${citationLine}</div>${editorialTail}`;
    };

    const splitCitedSourceVariants = (text) => {
      const split = splitQuoteLines(text);
      if (!split.tupi || !split.pt || !split.citation) return null;
      const variants = split.tupi.match(/^([\s\S]+?)\s+(\([^()]+\))\s+ou\s+([\s\S]+)$/i);
      if (!variants || !isSourceCitation(variants[2])) return null;
      return [
        { tupi: variants[1].trim(), pt: split.pt, citation: variants[2] },
        { tupi: variants[3].trim(), pt: split.pt, citation: split.citation },
      ];
    };

    const splitSharedCitationPairs = (text) => {
      if (parseDialogue(text)) return null;
      const { body, citation } = extractTrailingCitation(text);
      const separators = findTranslationSeparators(text);
      if (!citation || separators.length < 2) return null;

      const pairs = [];
      let pairStart = 0;
      for (let idx = 0; idx < separators.length - 1; idx += 1) {
        const translationStart = separators[idx].index + separators[idx].length;
        const nextSeparator = separators[idx + 1].index;
        const between = body.slice(translationStart, nextSeparator);
        const sentenceBreaks = [...between.matchAll(/[.!?…][)\"'’”]?\s+/g)]
          .filter((sentenceBreak) => {
            const suffix = between
              .slice(sentenceBreak.index + sentenceBreak[0].length)
              .trim();
            return suffix && !/^\(ou\b/i.test(suffix);
          });
        if (!sentenceBreaks.length) return null;
        const boundary = translationStart
          + sentenceBreaks[sentenceBreaks.length - 1].index
          + sentenceBreaks[sentenceBreaks.length - 1][0].length;
        pairs.push(body.slice(pairStart, boundary).trim());
        pairStart = boundary;
      }
      pairs.push(body.slice(pairStart).trim());

      if (pairs.length !== separators.length || pairs.some((pair) => {
        const split = splitQuoteLines(pair);
        return !split.tupi || !split.pt || findTranslationSeparators(pair).length !== 1;
      })) {
        return null;
      }

      return pairs.map((pair) => `${pair} ${citation}`);
    };

    const buildQuoteBlocks = (text) => {
      const citedVariants = splitCitedSourceVariants(text);
      if (citedVariants) {
        return citedVariants.map((variant) => buildQuoteBlock(
          `${variant.tupi} - ${variant.pt} ${variant.citation}`
        )).join('<div class="quote-variant-separator">ou</div>');
      }
      const pairs = splitSharedCitationPairs(text);
      return pairs
        ? pairs.map((pair) => {
          const editorialLead = pair.match(
            /^((?:\.\s*)?\(\s*(?:seu|com\s+o\s+verbo|também|perguntando)\b[^)]*\)\s*:\s*)([\s\S]+)$/i
          );
          return editorialLead
            ? `${editorialLead[1]}${buildQuoteBlock(editorialLead[2])}`
            : buildQuoteBlock(pair);
        }).join('')
        : buildQuoteBlock(text);
    };

    const splitRelatedEntryTail = (text) => {
      const { body, citation } = extractTrailingCitation(text);
      if (!citation) return null;
      const boundary = body.match(/;\s*(?=<span class="related-entry-headword">)/i);
      if (!boundary) return null;
      return {
        before: body.slice(0, boundary.index).trim(),
        tail: body.slice(boundary.index + boundary[0].length).trim(),
        citation,
      };
    };

    const findColonOutside = (text) => {
      let elementDepth = 0;
      let parenDepth = 0;
      let bracketDepth = 0;
      for (let idx = 0; idx < text.length; idx += 1) {
        const ch = text[idx];
        if (ch === '<') {
          const tagMatch = text.slice(idx).match(/^<\/?[A-Za-z][^>]*>/);
          if (!tagMatch) continue;
          const tag = tagMatch[0];
          if (/^<\//.test(tag)) {
            elementDepth = Math.max(0, elementDepth - 1);
          } else if (!/^<(?:br|hr|img|input|meta|link)\b/i.test(tag) && !/\/>$/.test(tag)) {
            elementDepth += 1;
          }
          idx += tag.length - 1;
          continue;
        }
        if (elementDepth > 0) continue;
        if (ch === '(') {
          parenDepth += 1;
          continue;
        }
        if (ch === ')' && parenDepth > 0) {
          parenDepth -= 1;
          continue;
        }
        if (ch === ')' && bracketDepth > 0) {
          bracketDepth -= 1;
          continue;
        }
        if (ch === '[') {
          bracketDepth += 1;
          continue;
        }
        if (ch === ']' && bracketDepth > 0) {
          bracketDepth -= 1;
          continue;
        }
        if (ch === ']' && bracketDepth === 0 && parenDepth > 0) {
          parenDepth -= 1;
          continue;
        }
        if (ch === ':' && parenDepth === 0 && bracketDepth === 0) {
          return idx;
        }
      }
      return -1;
    };

    const isColonInsideCitedSource = (text, colonIndex) => {
      if (colonIndex === -1) return false;
      const left = text.slice(0, colonIndex).trim();
      const right = text.slice(colonIndex + 1).trim();
      const separators = findTranslationSeparators(right);
      if (separators.length !== 1 || !hasTrailingCitation(right)) return false;
      const sourceBeforeTranslation = right.slice(0, separators[0].index).trim();
      const plainLeft = stripTags(left).trim();
      const looksLikeEditorialLead = (
        /^(?:\.\s*)?(?:(?:\([^)]*\)\s*)*\[|(?:\([^)]*\)\s*)+-\s+|\(\s*xe\s*\)|\(\s*(?:seu|com\s+o\s+verbo|também|perguntando|faz)\b|-?\s*(?:o\s+mesmo\s+que|pode\b)|-\s*\d+[ªº]\s+p\.)/i.test(
          plainLeft
        )
        || /^(?:\([^)]*\)\s*)+$/.test(plainLeft)
      );
      return (
        !looksLikeEditorialLead
        && !/class="sense-(?:section-title|number|letter|definition)"/i.test(left)
        && findTranslationSeparators(left).length === 0
        && looksDistinctivelyTupiText(left)
        && (/[,.!?…]/.test(stripTags(left)) || stripTags(left).split(/\s+/).length >= 4)
        && (
          quoteStartRe.test(stripTags(sourceBeforeTranslation).trim())
          || (
            looksLikeTupiText(sourceBeforeTranslation)
            && !looksLikePortugueseText(sourceBeforeTranslation)
          )
        )
      );
    };

    const findCitedPairColonBoundary = (text) => {
      let candidateIndex = -1;
      let offset = 0;
      while (offset < text.length) {
        const relativeIndex = findColonOutside(text.slice(offset));
        if (relativeIndex === -1) return candidateIndex;
        const colonIndex = offset + relativeIndex;
        const right = text.slice(colonIndex + 1).trim();
        const separators = findTranslationSeparators(right);
        const pair = splitQuoteLines(right);
        const sourceBeforeTranslation = separators.length
          ? right.slice(0, separators[0].index).trim()
          : '';
        const colonInsideSource = isColonInsideCitedSource(text, colonIndex)
          || (
            candidateIndex !== -1
            && isColonInsideCitedSource(
              text.slice(candidateIndex + 1),
              colonIndex - candidateIndex - 1
            )
          );
        const glossContinuesToLaterColon = findColonOutside(sourceBeforeTranslation) !== -1
          && /^[a-zà-ÿ]/.test(stripTags(sourceBeforeTranslation).trim());
        const sourceParts = stripTags(sourceBeforeTranslation)
          .split(/;\s*/)
          .map((part) => part.trim())
          .filter(Boolean);
        const isInlineGlossTail = sourceParts.length >= 2
          && looksLikePortugueseText(sourceParts[0])
          && !looksDistinctivelyTupiText(sourceParts[0])
          && looksDistinctivelyTupiText(sourceParts[sourceParts.length - 1]);
        if (
          right
          && !/class="sense-(?:section-title|number|letter|definition)"/i.test(right)
          && hasTrailingCitation(right)
          && separators.length === 1
          && pair.tupi
          && pair.pt
          && !hasCitation(pair.tupi)
          && !colonInsideSource
          && !glossContinuesToLaterColon
          && !isInlineGlossTail
        ) {
          candidateIndex = colonIndex;
        }
        offset = colonIndex + 1;
      }
      return candidateIndex;
    };

    const splitAtSourceCitationBoundaries = (segment) => {
      const chunks = [];
      let chunkStart = 0;
      let parenStart = -1;
      let depth = 0;

      for (let idx = 0; idx < segment.length; idx += 1) {
        const ch = segment[idx];
        if (ch === '(') {
          if (depth === 0) parenStart = idx;
          depth += 1;
          continue;
        }
        if (ch !== ')' || depth === 0) continue;
        depth -= 1;
        if (depth !== 0 || parenStart === -1) continue;

        const citation = segment.slice(parenStart, idx + 1);
        if (!isSourceCitation(citation)) continue;

        const remainder = segment.slice(idx + 1);
        const plainRemainder = stripTags(remainder).trim();
        if (
          !plainRemainder
          || /^[;]+$/.test(plainRemainder)
        ) {
          continue;
        }

        // Consecutive bibliographic parentheses belong to the same example.
        const nextParenthetical = plainRemainder.match(/^\([^()]+\)/);
        if (nextParenthetical && isSourceCitation(nextParenthetical[0])) continue;

        const candidate = segment.slice(chunkStart, idx + 1);
        const colonIndex = findColonOutside(candidate);
        const plainCandidate = stripTags(candidate);
        const plainColonIndex = findColonOutside(plainCandidate);
        const candidateSeparators = findTranslationSeparators(plainCandidate);
        const colonBelongsToTranslation = plainColonIndex !== -1
          && candidateSeparators.length
          && candidateSeparators[0].index < plainColonIndex;
        const quotePart = colonIndex === -1 || colonBelongsToTranslation
          ? candidate
          : candidate.slice(colonIndex + 1);
        const plainQuotePart = stripTags(quotePart).trim();
        const separators = findTranslationSeparators(plainQuotePart);
        const dialogue = parseDialogue(plainQuotePart);
        if (!separators.length && !dialogue) continue;

        if (colonIndex === -1) {
          const firstSeparator = separators[0];
          const tupiSide = firstSeparator
            ? plainQuotePart.slice(0, firstSeparator.index).trim()
            : plainQuotePart;
          const startsLikeQuote = TUPI_START_RE.test(tupiSide)
            || quoteStartRe.test(tupiSide)
            || Boolean(dialogue);
          const linkedCandidatePair = /related-entry-headword/.test(candidate)
            && separators.length === 1
            && hasTrailingCitation(candidate);
          if (
            !startsLikeQuote
            || /[\])}]$/.test(tupiSide)
            || (
              /related-entry-headword/.test(candidate)
              && !linkedCandidatePair
            )
          ) {
            continue;
          }
        }

        chunks.push(candidate);
        const separator = segment.slice(idx + 1).match(/^\s*[,;:]\s*/);
        chunkStart = idx + 1 + (separator ? separator[0].length : 0);
      }

      if (!chunks.length) return [segment];
      chunks.push(segment.slice(chunkStart));
      return chunks.filter((chunk) => chunk.length > 0);
    };

    const splitAtGeneratedSenseBoundaries = (segment) => {
      const chunks = [];
      let chunkStart = 0;
      const boundaryRe = /(?:<br>)+(?=<span class="sense-(?:number|letter)">)/gi;
      let match;
      while ((match = boundaryRe.exec(segment)) !== null) {
        if (match.index > chunkStart) {
          chunks.push(segment.slice(chunkStart, match.index));
          chunkStart = match.index;
        }
        if (match.index === boundaryRe.lastIndex) boundaryRe.lastIndex += 1;
      }
      chunks.push(segment.slice(chunkStart));
      return chunks.filter(Boolean);
    };

    const mergeSourceContinuationSegments = (items) => {
      const merged = [];
      for (let idx = 0; idx < items.length; idx += 1) {
        const current = items[idx];
        const next = items[idx + 1];
        const plainCurrent = stripTags(current).trim();
        const plainNext = next ? stripTags(next).trim() : '';
        const containsSemanticMarkup = /class="sense-(?:section-title|number|letter|definition)"/i.test(
          current
        );
        const semanticQuoteTail = current.match(/<\/span>\s*:\s*([\s\S]+)$/i);
        const plainColonIndex = findColonOutside(plainCurrent);
        const plainColonTail = plainColonIndex === -1
          ? ''
          : plainCurrent.slice(plainColonIndex + 1).trim();
        const sourceCandidate = semanticQuoteTail
          ? stripTags(semanticQuoteTail[1]).trim()
          : (plainColonTail || plainCurrent);
        if (
          next
          && /;\s*$/.test(plainCurrent)
          && (!containsSemanticMarkup || semanticQuoteTail)
          && !hasCitation(plainCurrent)
          && countDash(sourceCandidate) === 0
          && (
            looksLikeTupiText(sourceCandidate)
            || (
              /^[A-ZÀ-ÖØ-ÞŶ]/.test(sourceCandidate)
              && /^[a-zà-ÿ]/.test(plainNext)
            )
          )
          && countDash(plainNext) === 1
        ) {
          merged.push(current + next);
          idx += 1;
          continue;
        }
        merged.push(current);
      }
      return merged;
    };

    const mergeQuotedSegments = (items) => {
      const merged = [];
      let idx = 0;
      const firstSourceCitation = (value) => {
        const matches = [...value.matchAll(/\([^()]*\)/g)];
        return matches.find((match) => isSourceCitation(match[0])) || null;
      };

      while (idx < items.length) {
        const segment = items[idx];
        const trimmed = stripTags(segment).trim();

        if (!hasCitation(trimmed)) {
          let combined = segment;
          let j = idx + 1;
          let foundCitation = false;

          while (j < items.length) {
            if (/class="sense-(?:section-title|number|letter|definition)"/i.test(items[j])) {
              break;
            }
            const nextPlain = stripTags(items[j]).trim();
            const nextCitation = firstSourceCitation(nextPlain);
            const textBeforeCitation = nextCitation
              ? nextPlain.slice(0, nextCitation.index)
              : nextPlain;
            if (countDash(textBeforeCitation) > 0 || parseDialogue(textBeforeCitation)) {
              break;
            }
            combined += items[j];
            if (nextCitation) {
              foundCitation = true;
              break;
            }
            j += 1;
          }

          if (foundCitation) {
            const initialDashCount = countDash(trimmed);
            const startsWithQuote = quoteStartRe.test(trimmed);
            const shouldMerge = (startsWithQuote && initialDashCount <= 1)
              || initialDashCount === 1;

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

    const splitSemanticDefinitionQuote = (core) => {
      const match = core.match(
        /^([\s\S]*?)<span class="sense-definition">([\s\S]+)<\/span>;?$/i
      );
      if (!match) return null;

      const prefix = match[1];
      const definitionAndQuote = match[2];
      const { body, citation } = extractTrailingCitation(definitionAndQuote);

      const separators = findTranslationSeparators(body);
      let definition = '';
      let quoteBody = '';

      if (separators.length >= 2) {
        const boundary = separators[separators.length - 2];
        definition = body.slice(0, boundary.index).trim();
        quoteBody = body.slice(boundary.index + boundary.length).trim();
      } else if (separators.length === 1) {
        const translationSeparator = separators[0];
        const sourceSide = body.slice(0, translationSeparator.index).trim();
        const translation = body
          .slice(translationSeparator.index + translationSeparator.length)
          .trim();
        const mixedBoundary = sourceSide.match(
          /^([\s\S]*(?:\.{3}|\)|\]))\s+((?:\.{3}|…)?[A-ZÀ-ÖØ-ÞŶ][\s\S]*[.!?…])$/
        );
        if (mixedBoundary) {
          definition = mixedBoundary[1].trim();
          quoteBody = `${mixedBoundary[2].trim()} - ${translation}`;
        } else if (/[.!?…][\"'’”]?$/.test(sourceSide) && translation) {
          quoteBody = body;
        } else {
          return null;
        }
      } else {
        return null;
      }

      if (!quoteBody) return null;
      const quoteText = citation ? `${quoteBody} ${citation}` : quoteBody;
      const split = splitQuoteLines(quoteText);
      if (!split.tupi || !split.pt) return null;
      return { prefix, definition, quoteText };
    };

    const parseSegment = (segment) => {
      const spacingMatch = segment.match(/^(\s*)((?:<br>)+)?(\s*)(.*?)(\s*)$/is);
      const brPrefix = spacingMatch
        ? `${spacingMatch[1]}${spacingMatch[2] || ''}`
        : '';
      const leadingSpace = spacingMatch ? spacingMatch[3] : '';
      const core = spacingMatch ? spacingMatch[4] : segment;
      const trailingSpace = spacingMatch ? spacingMatch[5] : '';
      const plainCore = stripTags(core);
      const trimmedCore = core.trim();
      const startsWithHeadwordLink = /^(?:;?\s*(?:<br>)?\s*)*<span class="related-entry-headword">/i.test(trimmedCore);
      const containsSenseMarkup = /class="sense-(?:section-title|number|letter|definition)"/i.test(core);
      const startsWithDialogue = !containsSenseMarkup
        && Boolean(parseDialogue(trimmedCore));
      const isWholeDelimited = (value, open, close) => {
        if (!value.startsWith(open) || !value.endsWith(close)) return false;
        let depth = 0;
        for (let idx = 0; idx < value.length; idx += 1) {
          if (value[idx] === open) depth += 1;
          if (value[idx] === close) depth -= 1;
          if (depth === 0 && idx < value.length - 1) return false;
        }
        return depth === 0;
      };
      const plainTrimmed = plainCore.trim();
      const bracketCandidate = plainTrimmed.replace(/^\.\s*/, '');
      const bracketedProse = isWholeDelimited(bracketCandidate, '[', ']')
        || isWholeDelimited(plainTrimmed, '(', ')');
      const startsWithBracketedCategory = /^\[\s*(?:adj|adv)\.?\s*:/i.test(plainTrimmed);

      if (startsWithBracketedCategory && !hasDash(plainCore)) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'quoteListStart',
          quoteText: '',
          startsWithLetter: false,
        };
      }

      if (bracketedProse) {
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

      const citedPairColonIndex = findCitedPairColonBoundary(core);
      if (citedPairColonIndex !== -1) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'colonQuote',
          left: core.slice(0, citedPairColonIndex + 1),
          quoteText: core.slice(citedPairColonIndex + 1).trim(),
          startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
        };
      }

      // Recognize a complete multi-turn example before the more general
      // definition/quote recovery.  Otherwise the several turn dashes can be
      // mistaken for nested definition separators.
      const earlyColonIndex = findColonOutside(core);
      if (earlyColonIndex !== -1) {
        const dialogueRight = core.slice(earlyColonIndex + 1).trim();
        if (parseDialogue(dialogueRight)) {
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'colonQuote',
            left: core.slice(0, earlyColonIndex + 1),
            quoteText: dialogueRight,
            startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
          };
        }
      }

      const headingQuoteMatch = core.match(
        /^(<div class="sense-section-title">[^<]+<\/div>)<span class="sense-definition">([\s\S]+)<\/span>;?$/i
      );
      if (headingQuoteMatch) {
        const quoteText = headingQuoteMatch[2].trim();
        const split = splitQuoteLines(quoteText);
        if (
          extractTrailingCitation(quoteText).citation
          && findTranslationSeparators(quoteText).length === 1
          && split.tupi
          && split.pt
          && !(
            stripTags(split.tupi).includes(';')
            && !/[.!?…]/.test(stripTags(split.tupi))
          )
        ) {
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'headingQuote',
            left: headingQuoteMatch[1],
            quoteText,
            startsWithLetter: false,
          };
        }
      }

      const semanticDefinitionQuote = splitSemanticDefinitionQuote(core);
      if (semanticDefinitionQuote) {
        const definitionHtml = semanticDefinitionQuote.definition
          ? `<span class="sense-definition">${semanticDefinitionQuote.definition}</span>`
          : '';
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'definitionQuote',
          left: `${semanticDefinitionQuote.prefix}${definitionHtml}`,
          quoteText: semanticDefinitionQuote.quoteText,
          startsWithLetter: false,
        };
      }

      // Related-entry source occasionally uses
      // "lemma - gloss - Tupi sentence - Portuguese translation (source)".
      // Keep the lemma/gloss as prose and promote only the final cited pair.
      if (startsWithHeadwordLink) {
        const { body, citation } = extractTrailingCitation(core);
        const separators = findTranslationSeparators(body);
        if (citation && separators.length === 3) {
          const sourceStart = separators[1].index + separators[1].length;
          const source = body.slice(sourceStart, separators[2].index).trim();
          const portuguese = body
            .slice(separators[2].index + separators[2].length)
            .trim();
          if (
            source
            && portuguese
            && /[.!?…][\"'’”]?$/.test(stripTags(source))
            && !/^v\.\s*$/i.test(stripTags(portuguese))
          ) {
            const relatedPrefix = body.slice(0, separators[1].index).trim();
            return {
              segment,
              brPrefix,
              leadingSpace,
              core,
              trailingSpace,
              plainCore,
              startsWithHeadwordLink,
              type: 'relatedDefinitionQuote',
              left: /:\s*$/.test(stripTags(relatedPrefix))
                ? relatedPrefix
                : `${relatedPrefix}:`,
              quoteText: `${source} - ${portuguese} ${citation}`,
              startsWithLetter: false,
            };
          }
        }
      }

      let colonIndex = findColonOutside(core);
      if (isColonInsideCitedSource(core, colonIndex)) {
        colonIndex = -1;
      }
      const coreSeparators = findTranslationSeparators(core);
      const firstCoreSeparator = coreSeparators[0];
      const explicitCitedPairBeforeColon = (() => {
        if (
          colonIndex === -1
          || !firstCoreSeparator
          || firstCoreSeparator.index >= colonIndex
          || !hasTrailingCitation(core)
        ) {
          return false;
        }
        const source = stripTags(core.slice(0, firstCoreSeparator.index)).trim();
        return TUPI_START_RE.test(source)
          && /(?:[îûŷẽõ]|gû|kû|nh|mb|nd|[aeiouáéíóú]['’])/i.test(source);
      })();
      if (
        colonIndex !== -1
        && !core.includes('<')
        && coreSeparators.length
        && (firstCoreSeparator.compact || explicitCitedPairBeforeColon)
        && coreSeparators[0].index < colonIndex
      ) {
        // A colon in the Portuguese half (for example "-Disseste:") is
        // punctuation, not a definition/example boundary.
        colonIndex = -1;
      }
      if (colonIndex !== -1) {
        let left = core.slice(0, colonIndex + 1);
        let rightStart = colonIndex + 1;
        while (/\s/.test(core[rightStart] || '')) rightStart += 1;
        let right = core.slice(rightStart).trimEnd();
        let plainRight = stripTags(right);

        const startsWithSenseMarker = (() => {
          if (plainRight.trim().match(/^(\d+|[a-z])\)/i)) {
            return true;
          }
          return /<span class="sense-(number|letter)">/i.test(right);
        })();

        const secondaryIndex = findColonOutside(right);
        const firstRightSeparator = findTranslationSeparators(right)[0];
        const hasDanglingGlossFragment = containsSenseMarkup
          && /^[a-zà-ÿ][^:]*\)\s*:/.test(plainRight.trim());
        const hasLeadingSemanticDefinition = containsSenseMarkup
          && /<span class="sense-definition">[\s\S]*<\/span>\s*:/.test(
            right.slice(0, secondaryIndex + 1)
          );
        const hasLeadingGlossBeforeExample = secondaryIndex !== -1
          && /^[a-zà-ÿ]/.test(
            stripTags(right.slice(0, secondaryIndex)).trim()
          );
        if (
          secondaryIndex !== -1
          && (
            startsWithSenseMarker
            || hasDanglingGlossFragment
            || hasLeadingSemanticDefinition
            || hasLeadingGlossBeforeExample
          )
          && (!firstRightSeparator || secondaryIndex < firstRightSeparator.index)
        ) {
            const newColonPos = rightStart + secondaryIndex;
            const candidateRight = core.slice(newColonPos + 1).trim();
            const candidatePlainRight = stripTags(candidateRight);
            const candidateStartsDialogue = Boolean(parseDialogue(candidatePlainRight.trim()));
            const candidatePair = splitQuoteLines(candidateRight);
            const validatedGlossBoundary = !hasLeadingGlossBeforeExample || (
              hasTrailingCitation(candidateRight)
              && candidatePair.tupi
              && candidatePair.pt
              && /[.!?…][\"'’”]?$/.test(stripTags(candidatePair.tupi).trim())
            );
            if (
              candidateRight
              && validatedGlossBoundary
              && (hasDash(candidatePlainRight) || candidateStartsDialogue)
            ) {
              left = core.slice(0, newColonPos + 1);
              right = candidateRight;
              plainRight = candidatePlainRight;
            }
        }

        const implicitRightPair = splitImplicitCitedPair(right);
        if (right && implicitRightPair) {
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
            quoteText: implicitRightPair.quoteText,
            startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
          };
        }

        const rightStartsDialogue = Boolean(parseDialogue(plainRight.trim()));
        const rightPair = splitQuoteLines(right);
        const rightSourceParts = stripTags(rightPair.tupi)
          .split(/;\s*/)
          .map((part) => part.trim())
          .filter(Boolean);
        const firstGlossColon = rightSourceParts.length
          ? findColonOutside(rightSourceParts[0])
          : -1;
        const firstInlineGloss = firstGlossColon === -1
          ? ''
          : rightSourceParts[0].slice(firstGlossColon + 1).trim();
        const isInlineGlossList = rightSourceParts.length === 2
          && firstInlineGloss
          && looksLikePortugueseText(firstInlineGloss)
          && !looksDistinctivelyTupiText(firstInlineGloss)
          && looksDistinctivelyTupiText(rightSourceParts[rightSourceParts.length - 1]);
        if (isInlineGlossList) {
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'inlineGlossPairs',
            left,
            inlinePairs: [
              {
                source: rightSourceParts[0].slice(0, firstGlossColon).trim(),
                portuguese: firstInlineGloss,
                citation: rightPair.citation,
              },
              {
                source: rightSourceParts[1],
                portuguese: stripTags(rightPair.pt).trim(),
                citation: rightPair.citation,
              },
            ],
            quoteText: right,
            startsWithLetter: false,
          };
        }
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

        if (!right && colonIndex === core.trimEnd().length - 1) {
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'quoteListStart',
            quoteText: '',
            startsWithLetter: false,
          };
        }
      }

      // One attested example omits the usual translation dash after an
      // ellipsis ("Emonãnamo, xe ruri... Portanto, eu vim.").  Recover only
      // that citation-backed shape so an ordinary ellipsis in prose remains
      // prose rather than becoming a fabricated bilingual pair.
      if (!containsSenseMarkup && !hasDash(plainCore)) {
        const { body: uncitedBody, citation } = extractTrailingCitation(core);
        const implicitPair = citation && uncitedBody.match(
          /^([\s\S]+?(?:\.{3}|…))\s+([A-ZÀ-ÖØ-ÞŶ][\s\S]+)$/
        );
        if (implicitPair && TUPI_START_RE.test(stripTags(implicitPair[1]).trim())) {
          const quoteText = `${implicitPair[1].trim()} - ${implicitPair[2].trim()} ${citation}`;
          return {
            segment,
            brPrefix,
            leadingSpace,
            core,
            trailingSpace,
            plainCore,
            startsWithHeadwordLink,
            type: 'quote',
            quoteText,
            startsWithLetter: true,
          };
        }
      }

      if (hasDash(plainCore) && !containsSenseMarkup) {
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

      const implicitPair = !containsSenseMarkup
        ? splitImplicitCitedPair(core)
        : null;
      if (implicitPair) {
        return {
          segment,
          brPrefix,
          leadingSpace,
          core,
          trailingSpace,
          plainCore,
          startsWithHeadwordLink,
          type: 'implicitQuote',
          quoteText: implicitPair.quoteText,
          startsWithLetter: TUPI_START_RE.test(plainCore.trim()),
        };
      }

      if (
        hasTrailingCitation(plainCore)
        && quoteStartRe.test(plainCore.trim())
        && !containsSenseMarkup
      ) {
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

    const senseDelimitedSegments = segments.flatMap(splitAtGeneratedSenseBoundaries);
    const citationDelimitedSegments = senseDelimitedSegments.flatMap(splitAtSourceCitationBoundaries);
    const sourceContinuationSegments = mergeSourceContinuationSegments(
      citationDelimitedSegments
    );
    const mergedSegments = mergeQuotedSegments(sourceContinuationSegments);
    const finalSegments = mergedSegments.flatMap(splitAtSourceCitationBoundaries);
    const editorialDelimitedSegments = finalSegments.flatMap((segment) => {
      const noteMatch = segment.match(
        /(\s+\(\s*V\.\s*(?:tb\.\s*)?[^()]*\))\s*$/i
      );
      if (!noteMatch) return [segment];
      const prefix = segment.slice(0, noteMatch.index).trimEnd();
      return hasTrailingCitation(prefix)
        ? [prefix, noteMatch[1]]
        : [segment];
    });
    const parsedSegments = editorialDelimitedSegments.map(parseSegment);

    // A source can give a second cited Portuguese gloss for the immediately
    // preceding form without repeating that form (for example, "kóbo - nas
    // roças (...); pelas roças (...)").  Duplicate the source side in the
    // rendered card instead of leaving the second gloss orphaned.
    for (let idx = 1; idx < parsedSegments.length; idx += 1) {
      const current = parsedSegments[idx];
      const previous = parsedSegments[idx - 1];
      if (
        current.type !== 'other'
        || previous.startsWithHeadwordLink
        || !previous.quoteText
        || hasDash(current.core)
        || !hasTrailingCitation(current.core)
      ) {
        continue;
      }
      const currentPlain = stripTags(current.core).trim();
      const previousPair = splitQuoteLines(previous.quoteText);
      if (
        !/^[a-zà-ÿ]/.test(currentPlain)
        || looksDistinctivelyTupiText(currentPlain)
        || !previousPair.tupi
        || !previousPair.pt
      ) {
        continue;
      }
      current.type = 'quote';
      current.quoteText = `${previousPair.tupi} - ${normalizeQuoteText(current.core)}`;
      current.startsWithLetter = true;
    }

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
      if (/\([^()]+\)\s*$/.test(stripTags(normalized))) {
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

      if (seg.type === 'quoteListStart') {
        inQuoteList = true;
        formattedSegments.push(seg.segment);
        if (seg.plainCore.trim()) seenContent = true;
        continue;
      }

      if (seg.type === 'inlineGlossPairs') {
        inQuoteList = true;
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${seg.left}${seg.inlinePairs
            .map((pair) =>
              buildQuoteBlock(
                `${pair.source} - ${pair.portuguese} ${pair.citation}`
              )
            )
            .join('')}${seg.trailingSpace}`
        );
        seenContent = true;
        continue;
      }

      if (seg.type === 'colonQuote') {
        const quoteText = ensureCitation(seg.quoteText, idx + 1);
        const relatedTail = splitRelatedEntryTail(quoteText);
        if (relatedTail) {
          const firstQuoteText = `${relatedTail.before} ${relatedTail.citation}`;
          const firstPair = splitQuoteLines(firstQuoteText);
          const tailText = `${relatedTail.tail} ${relatedTail.citation}`;
          const tailPair = splitQuoteLines(tailText);
          if (
            firstPair.tupi
            && !firstPair.pt
            && tailPair.tupi
            && tailPair.pt
          ) {
            formattedSegments.push(
              `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlock(
                `${firstPair.tupi} - ${tailPair.pt} ${relatedTail.citation}`
              )}${buildQuoteBlock(tailText)}${seg.trailingSpace}`
            );
            inQuoteList = true;
            seenContent = true;
            continue;
          }
          const firstIsSentenceExample = /[.!?…]["'’”]?$/.test(
            stripTags(firstPair.tupi).trim()
          );
          formattedSegments.push(
            firstIsSentenceExample
              ? `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlocks(firstQuoteText)} ${tailText}${seg.trailingSpace}`
              : `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlocks(firstQuoteText)}${buildQuoteBlocks(tailText)}${seg.trailingSpace}`
          );
          inQuoteList = !firstIsSentenceExample;
          seenContent = true;
          continue;
        }
        inQuoteList = true;
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
        );
        seenContent = true;
        continue;
      }

      if (
        seg.type === 'headingQuote'
        || seg.type === 'definitionQuote'
        || seg.type === 'relatedDefinitionQuote'
      ) {
        inQuoteList = true;
        const quoteText = ensureCitation(seg.quoteText, idx + 1);
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${seg.left}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
        );
        seenContent = true;
        continue;
      }

      // A complete, cited bilingual pair is an example regardless of whether
      // a preceding colon survived the source's loose punctuation.  Requiring
      // both sides plus a credible trailing citation keeps hyphenated prose
      // and related-entry labels out of quote cards.
      if (
        seg.type === 'quote'
        && hasTrailingCitation(seg.quoteText)
      ) {
        const pair = splitQuoteLines(seg.quoteText);
        const source = stripTags(pair.tupi).replace(/^\s*-\s*/, '').trim();
        const portuguese = stripTags(pair.pt).trim();
        const relatedHeadwordCount = (
          seg.quoteText.match(/class="related-entry-headword"/gi) || []
        ).length;
        const linkedPhraseLooksLikeExample = seg.startsWithHeadwordLink
          && relatedHeadwordCount === 1
          && !/;\s*<span class="related-entry-headword">/i.test(seg.quoteText)
          && source.split(/\s+/).length >= 4
          && /^[A-ZÀ-ÖØ-ÞŶ]/.test(portuguese);
        if (
          pair.tupi
          && pair.pt
          && (TUPI_START_RE.test(source) || quoteStartRe.test(source))
          && !/^v\.\s*$/i.test(portuguese)
          && (!relatedHeadwordCount || linkedPhraseLooksLikeExample)
        ) {
          const quoteText = normalizeQuoteText(seg.quoteText).replace(
            /<span class="related-entry-headword"><a\b[^>]*>([\s\S]*?)<\/a><\/span>/i,
            '$1'
          );
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
          );
          inQuoteList = true;
          seenContent = true;
          continue;
        }
      }

      if (inQuoteList) {
        if (
          (seg.type === 'quote' || seg.type === 'dialogue' || seg.type === 'implicitQuote')
          && !seg.startsWithHeadwordLink
          && !/class="related-entry-headword"/i.test(seg.quoteText)
        ) {
          const quoteText = ensureCitation(seg.quoteText, idx + 1);
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
          );
          continue;
        }
        inQuoteList = false;
      }

      if ((seg.type === 'dialogue' || seg.type === 'quote') && !seg.startsWithHeadwordLink) {
        const trimmedQuote = seg.quoteText.trim();
        if (parseDialogue(trimmedQuote)) {
          const quoteText = ensureCitation(seg.quoteText, idx + 1);
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
          );
          seenContent = true;
          continue;
        }
      }

      if (
        !seenContent
        && seg.type === 'quote'
        && seg.startsWithLetter
        && hasCitation(seg.quoteText)
        && !seg.startsWithHeadwordLink
        && !/class="related-entry-headword"/i.test(seg.quoteText)
      ) {
        const quoteText = normalizeQuoteText(seg.quoteText);
        formattedSegments.push(
          `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlocks(quoteText)}${seg.trailingSpace}`
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
      const formatted = formatVerbeteSection(before, true);
      return nota ? `${formatted}<br>${nota}` : formatted;
    }

    const formattedMain = sections
      .map((section, index) => {
        let sectionWithLinks = index === 0 ? section : linkRelatedHeadwords(section);
        if (index !== 0) {
          sectionWithLinks = sectionWithLinks.replace(/^\s*(<br>\s*)+/, '');
        }
        const formattedSection = formatVerbeteSection(sectionWithLinks, index === 0);
        if (index === 0) {
          return formattedSection;
        }
        const formattedWithBreaks = formattedSection.replace(
          /;\s*(?=<span class="related-entry-headword">)/g,
          ';<br>'
        );
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

    const query = normalizeApostrophes(searchInput.value.trim());
    searchInput.value = query;
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
