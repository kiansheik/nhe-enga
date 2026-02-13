(() => {
  'use strict';

  const DATA_PATH = 'docs/dict-conjugated.json.gz';
  const NEO_PATH = '/nhe-enga/neologisms.csv';

  const MODES = ['indicativo', 'permissivo', 'circunstancial', 'gerundio', 'imperativo', 'conjuntivo'];

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
    return data.map((item) => ({
      first_word: item.f || '',
      optional_number: item.o || '',
      definition: item.d || '',
      con: item.c || '',
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

    const subjectsVals = Object.entries(subjMap)
      .filter((item) => uniqueSubjects.has(item[1]))
      .map(([_, value]) => value);

    const objectsVals = Object.entries(objMap)
      .filter((item) => uniqueObjects.has(item[1]))
      .map(([_, value]) => value);

    const subjects = Object.entries(subjMap)
      .filter((item) => uniqueSubjects.has(item[1]))
      .map(([key]) => key);

    const objects = Object.entries(objMap)
      .filter((item) => uniqueObjects.has(item[1]))
      .map(([key]) => key);

    let htmlString = `<table class="options-container" id="conj-${unId}">`;
    htmlString += `<tr><th>
        Modo<br><select id="mode-${unId}" class="option">
        <!-- Add options dynamically using JavaScript -->
    </select><br>
        <input type="checkbox" id="negarCheckbox-${unId}" ${negar ? 'checked' : ''} name="negarCheckbox">
        <label for="negarCheckbox">Negar</label>
    </th><th class="label" style="background-color: #e4ffe4;" colspan="${objects.length + 1}">Objeto</th></tr>`;
    htmlString += `<th style="background-color: #fef9c3ab;" class="label">
        Sujeito</th>`;

    objects.forEach((object) => {
      htmlString += `<th style="background-color: #e4ffe4;">${object}</th>`;
    });

    htmlString += '</tr>';

    for (let i = 0; i < subjects.length; i++) {
      htmlString += `<tr><th style="background-color: #fef9c3ab;">${subjects[i]}</th>`;
      const subj = subjectsVals[i];
      for (let j = 0; j < objects.length; j++) {
        const obj = objectsVals[j];
        const conj = conjugations[JSON.stringify([subj, obj])] || '-';
        htmlString += `<td>${conj}</td>`;
      }
      htmlString += '</tr>';
    }

    htmlString += '</table>';
    return htmlString;
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
      tempContainer.firstChild.style.display = 'flex';
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

  function linkRelatedHeadwords(section) {
    let output = '';
    let i = 0;
    let parenDepth = 0;
    let atEntryStart = true;
    const len = section.length;

    const isLetterStart = (char) => char && /[A-Za-zÀ-ÿ]/.test(char);
    const isHeadChar = (char) => char && /[A-Za-zÀ-ÿ'’\\-]/.test(char);

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

    const isBoundary = (char) => char === undefined || /[\s.;:!?]/.test(char);
    const segments = [];

    while (i < section.length) {
      const char = section[i];

      if (parenDepth === 0) {
        const prevChar = section[i - 1];
        const boundaryOk = isBoundary(prevChar);

        if (boundaryOk) {
          const numberMatch = section.slice(i).match(/^(\d+)\)/);
          if (numberMatch) {
            const numberValue = Number(numberMatch[1]);
            if (Number.isFinite(numberValue) && numberValue === expectedNumber) {
              if (definitionOpen) {
                output += '</span>';
                definitionOpen = false;
              }
              if (output.length && !output.endsWith('<br>')) {
                output += '<br>';
              }
              output += `<span class="sense-number">${numberMatch[0]}</span>`;
              output += '<span class="sense-definition">';
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
              if (output.length && !output.endsWith('<br>')) {
                output += '<br>';
              }
              output += `<span class="sense-letter">${letterMatch[0]}</span>`;
              output += '<span class="sense-definition">';
              definitionOpen = true;
              expectedLetter = String.fromCharCode(expectedLetter.charCodeAt(0) + 1);
              i += letterMatch[0].length;
              continue;
            }
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

    const hasDash = (text) => /\s-\s/.test(normalizeQuoteText(text));
    const hasCitation = (text) => /\([^()]*\)/.test(normalizeQuoteText(text));

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
        return { tupi: body, pt: '', citation };
      }

      return {
        tupi: body.slice(0, dashIndex).trim(),
        pt: body.slice(dashIndex + 3).trim(),
        citation,
      };
    };

    const buildQuoteBlock = (text) => {
      const { tupi, pt, citation } = splitQuoteLines(text);
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

    const parseSegment = (segment) => {
      const brMatch = segment.match(/^((?:<br>)+)(.*)$/i);
      const brPrefix = brMatch ? brMatch[1] : '';
      const remainder = brMatch ? brMatch[2] : segment;
      const spacingMatch = remainder.match(/^(\s*)(.*?)(\s*)$/s);
      const leadingSpace = spacingMatch ? spacingMatch[1] : '';
      const core = spacingMatch ? spacingMatch[2] : remainder;
      const trailingSpace = spacingMatch ? spacingMatch[3] : '';
      const plainCore = core.replace(/<[^>]*>/g, '');
      const trimmedCore = core.trim();
      const startsWithHeadwordLink = trimmedCore.startsWith('<span class="related-entry-headword">');

      const colonIndex = findColonOutside(core);
      if (colonIndex !== -1) {
        const left = core.slice(0, colonIndex + 1);
        const right = core.slice(colonIndex + 1).trim();
        const plainRight = right.replace(/<[^>]*>/g, '');
        if (right && hasDash(plainRight)) {
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
            startsWithLetter: /^[A-Za-zÀ-ÿ]/.test(plainCore.trim()),
          };
        }
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
          startsWithLetter: /^[A-Za-zÀ-ÿ]/.test(plainCore.trim()),
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

    const parsedSegments = segments.map(parseSegment);

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
        if (seg.type === 'quote' && !seg.startsWithHeadwordLink) {
          const quoteText = ensureCitation(seg.quoteText, idx + 1);
          formattedSegments.push(
            `${seg.brPrefix}${seg.leadingSpace}${buildQuoteBlock(quoteText)}${seg.trailingSpace}`
          );
          continue;
        }
        inQuoteList = false;
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
    const sections = splitByBullet(definition);
    if (sections.length <= 1) {
      return formatVerbeteSection(definition);
    }

    return sections
      .map((section, index) => {
        let sectionWithLinks = index === 0 ? section : linkRelatedHeadwords(section);
        if (index !== 0) {
          sectionWithLinks = sectionWithLinks.replace(/^\s*(<br>\s*)+/, '');
        }
        const formattedSection = formatVerbeteSection(sectionWithLinks);
        if (index === 0) {
          return formattedSection;
        }
        return `<div class="sense-section-title">Verbetes relacionados:</div>${formattedSection}`;
      })
      .join('');
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
        optionsContainer.style.display =
          optionsContainer.style.display === 'none' || optionsContainer.style.display === '' ? 'flex' : 'none';
      });
    }

    toggleContainer.classList.toggle('disabled');

    const newPosition = !toggleContainer.classList.contains('disabled') ? '100%' : '0';
    toggleBall.style.transform = `translate(${newPosition}, -50%)`;
    setCookie('conjugationToggle', toggleContainer.classList.contains('disabled') ? 'disabled' : 'enabled', 30);
  }

  function renderResults(results, query) {
    resultsDiv.style.display = 'block';

    if (!results.length) {
      resultsDiv.textContent = 'Não foram encontrados resultados.';
      return;
    }

    const fragment = document.createDocumentFragment();
    const escapedQuery = escapeRegExp(query);
    const highlightRegex = new RegExp(`(?<!=\"[^\"]*)(${escapedQuery})(?![^\"]*\")`, 'ig');

    results.forEach((result) => {
      const entry = document.createElement('div');
      entry.classList.add('entry');

      const preview = document.createElement('div');
      preview.classList.add('preview');
      if (result.type !== undefined) {
        preview.classList.add(result.type);
      }

      const linkedDefinition = linkSources(formatVerbeteDefinition(result.definition))
        .replace(highlightRegex, '<span class="highlighted">$1</span>');

      const link = document.createElement('a');
      link.href = `${window.location.pathname}?query=${encodeURIComponent(result.first_word)}`;
      link.innerText = result.first_word;
      link.classList.add('search-link');

      const optionalNumberSup = document.createElement('sup');
      optionalNumberSup.innerText = result.optional_number;

      preview.appendChild(link);
      preview.appendChild(optionalNumberSup);
      preview.innerHTML += ` ${linkedDefinition}`;

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
    jsonData = [...compressedData, ...neos];
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
