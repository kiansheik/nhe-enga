/* Source-only VLB search. Orthographic scores are retrieval costs, not identity. */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.VLBSearch = api;
})(typeof window === "object" ? window : null, function () {
  "use strict";

  const WORD_RE = /\p{L}[\p{L}\p{M}]*(?:['’ʼ-]\p{L}[\p{L}\p{M}]*)*/gu;
  const MARK_RE = /\p{M}/u;
  const APOSTROPHES_RE = /[’‘‛ʼʻ]/g;
  const LABELS = {
    "vlb-whole": "VLB · forma exata",
    "portuguese-whole": "Português · palavra exata",
    "transcription-whole": "Transcrição · palavra exata",
    "vlb-inside": "VLB · dentro de palavra",
    "portuguese-inside": "Português · dentro de palavra",
    "transcription-inside": "Transcrição · dentro de palavra",
    probable: "Navarro → VLB · grafia provável",
  };

  function normalizeForm(text) {
    return String(text || "").replace(APOSTROPHES_RE, "'")
      .toLocaleLowerCase("pt-BR").normalize("NFC").trim();
  }

  function words(text) {
    return normalizeForm(text).match(WORD_RE) || [];
  }

  function graphemes(text) {
    const clusters = [];
    for (const char of normalizeForm(text).normalize("NFD")) {
      if (MARK_RE.test(char) && clusters.length) clusters[clusters.length - 1] += char;
      else clusters.push(char);
    }
    return clusters.map(cluster => cluster.normalize("NFC"));
  }

  function splitRecord(row) {
    const text = String(row?.text || "");
    const divider = text.indexOf("—");
    if (divider < 0) {
      const tokens = words(text);
      return {portuguese: "", vlb: "", transcription: text, portugueseTokens: [],
        vlbTokens: [], transcriptionTokens: tokens};
    }
    const portuguese = text.slice(0, divider);
    const vlb = text.slice(divider + 1);
    return {portuguese, vlb, transcription: "", portugueseTokens: words(portuguese),
      vlbTokens: words(vlb), transcriptionTokens: []};
  }

  function startsWithTokens(tokens, query) {
    return query.length <= tokens.length && query.every((token, index) => tokens[index] === token);
  }

  function containsPhrase(tokens, query) {
    if (!query.length || query.length > tokens.length) return false;
    outer: for (let start = 0; start <= tokens.length - query.length; start++) {
      for (let offset = 0; offset < query.length; offset++) {
        if (tokens[start + offset] !== query[offset]) continue outer;
      }
      return true;
    }
    return false;
  }

  function literalCandidate(record, queryTokens) {
    const parts = [
      ["vlb", record.vlbTokens],
      ["portuguese", record.portugueseTokens],
      ["transcription", record.transcriptionTokens],
    ];
    const candidates = [];
    for (const [side, tokens] of parts) {
      if (!tokens.length) continue;
      if (containsPhrase(tokens, queryTokens)) {
        const start = tokens.findIndex((_, index) =>
          queryTokens.every((token, offset) => tokens[index + offset] === token));
        candidates.push({side, scope: "whole", matchedForm: tokens.slice(start, start + queryTokens.length).join(" "),
          prefix: startsWithTokens(tokens, queryTokens)});
      } else if (queryTokens.length === 1) {
        const match = tokens.find(token => token !== queryTokens[0] && token.includes(queryTokens[0]));
        if (match) candidates.push({side, scope: "inside", matchedForm: match, prefix: false});
      }
    }
    if (!candidates.length) return null;
    const scopeRank = {whole: 0, inside: 1};
    const sideRank = {vlb: 0, portuguese: 1, transcription: 2};
    candidates.sort((left, right) => scopeRank[left.scope] - scopeRank[right.scope] ||
      Number(right.prefix) - Number(left.prefix) || sideRank[left.side] - sideRank[right.side]);
    return candidates[0];
  }

  function baseMarks(grapheme) {
    const expanded = grapheme.normalize("NFD");
    return [expanded.slice(0, 1), new Set(Array.from(expanded.slice(1)))];
  }

  function compileModel(model) {
    if (!model || !Array.isArray(model.rules)) throw new TypeError("Modelo ortográfico inválido.");
    const costs = model.default_costs || {};
    const editCost = Number(costs.edit ?? 1);
    const stressCost = Number(costs.stress_mark_difference ?? .26);
    const nasalCost = Number(costs.nasal_mark_difference ?? .75);
    const rulesByEnd = new Map();
    const deletions = new Map();
    for (const item of model.rules) {
      const source = item.from === " " ? [" "] : graphemes(item.from);
      const target = graphemes(item.to);
      const cost = Number(item.cost);
      if (!source.length || !Number.isFinite(cost) || cost < 0) continue;
      const rule = {id: item.id, source, target, cost, context: item.context || {}};
      if (!target.length) {
        if (source.length !== 1) continue;
        if (!deletions.has(source[0]) || deletions.get(source[0]).cost > cost) deletions.set(source[0], rule);
      } else {
        const key = `${source.at(-1)}\u0000${target.at(-1)}`;
        if (!rulesByEnd.has(key)) rulesByEnd.set(key, []);
        rulesByEnd.get(key).push(rule);
      }
    }
    const cache = new Map();

    function substitutionCost(source, target) {
      if (source === target) return 0;
      const [sourceBase, sourceMarks] = baseMarks(source);
      const [targetBase, targetMarks] = baseMarks(target);
      if (sourceBase === targetBase) {
        if (sourceMarks.has("\u0303") !== targetMarks.has("\u0303")) return nasalCost;
        return stressCost;
      }
      return editCost;
    }

    function contextMatches(rule, source, target, i, j) {
      const context = rule.context;
      const targetAfter = context.target_after_bases;
      if (targetAfter !== undefined && (j === target.length || !targetAfter.includes(baseMarks(target[j])[0]))) return false;
      const targetForbidden = context.target_after_not_bases;
      if (targetForbidden !== undefined && j < target.length && targetForbidden.includes(baseMarks(target[j])[0])) return false;
      const sourceAfter = context.source_after_bases;
      if (sourceAfter !== undefined && (i === source.length || !sourceAfter.includes(baseMarks(source[i])[0]))) return false;
      if (context.source_end && i !== source.length) return false;
      if (context.target_end && j !== target.length) return false;
      return true;
    }

    function score(modernText, historicalText) {
      const modern = normalizeForm(modernText);
      const historical = normalizeForm(historicalText);
      if (modern === historical) return 0;
      const key = `${modern}\u0000${historical}`;
      if (cache.has(key)) return cache.get(key);
      const source = graphemes(modern);
      const target = graphemes(historical);
      const rows = Array.from({length: source.length + 1}, () => Array(target.length + 1).fill(0));
      for (let i = 1; i <= source.length; i++) {
        const deletion = deletions.get(source[i - 1]);
        rows[i][0] = rows[i - 1][0] + Math.min(editCost, deletion?.cost ?? editCost);
      }
      for (let j = 1; j <= target.length; j++) rows[0][j] = rows[0][j - 1] + editCost;
      for (let i = 1; i <= source.length; i++) {
        const sourceUnit = source[i - 1];
        const deletion = deletions.get(sourceUnit);
        const deletionCost = Math.min(editCost, deletion?.cost ?? editCost);
        for (let j = 1; j <= target.length; j++) {
          const targetUnit = target[j - 1];
          let best = rows[i - 1][j - 1] + substitutionCost(sourceUnit, targetUnit);
          best = Math.min(best, rows[i - 1][j] + deletionCost, rows[i][j - 1] + editCost);
          const key = `${sourceUnit}\u0000${targetUnit}`;
          for (const rule of rulesByEnd.get(key) || []) {
            const sourceStart = i - rule.source.length;
            const targetStart = j - rule.target.length;
            if (sourceStart < 0 || targetStart < 0) continue;
            if (!rule.source.every((unit, index) => source[sourceStart + index] === unit) ||
                !rule.target.every((unit, index) => target[targetStart + index] === unit) ||
                !contextMatches(rule, source, target, i, j)) continue;
            best = Math.min(best, rows[sourceStart][targetStart] + rule.cost);
          }
          rows[i][j] = best;
        }
      }
      const normalized = Math.min(1, rows[source.length][target.length] /
        Math.max(source.length, target.length, 1));
      if (cache.size >= 100000) cache.clear();
      cache.set(key, normalized);
      return normalized;
    }

    return {score, direction: model.direction, weightsAreProbabilities: model.weights_are_probabilities === true};
  }

  function buildIndex(rows) {
    const records = [];
    const vlbTokenRecords = new Map();
    for (const source of rows || []) {
      const parts = splitRecord(source);
      const record = {source, ...parts};
      records.push(record);
      for (const token of new Set(parts.vlbTokens)) {
        if (!vlbTokenRecords.has(token)) vlbTokenRecords.set(token, []);
        vlbTokenRecords.get(token).push(record);
      }
    }
    return {records, vlbTokenRecords};
  }

  function firstPageId(source) {
    const page = source?.page_ids?.[0];
    return typeof page === "string" ? page : page?.id || null;
  }

  function directPageId(record, queryTokens, match) {
    for (const fragment of record.source.fragments || []) {
      const fragmentMatch = literalCandidate({...splitRecord({text: fragment.text}), source: record.source}, queryTokens);
      if (fragmentMatch?.scope === match.scope) return fragment.page_id || fragment.id || firstPageId(record.source);
    }
    return firstPageId(record.source);
  }

  function probablePageId(record, token) {
    for (const fragment of record.source.fragments || []) {
      if (words(fragment.text).includes(token)) return fragment.page_id || fragment.id || firstPageId(record.source);
    }
    return firstPageId(record.source);
  }

  function directResult(record, match, queryTokens) {
    const key = `${match.side}-${match.scope}`;
    return {source: record.source, sourceId: record.source.source_id || record.source.id,
      sourceLine: record.source.source_line, pageId: directPageId(record, queryTokens, match),
      kind: key, side: match.side, scope: match.scope,
      queryPath: "literal", matchedForm: match.matchedForm, cost: null, prefix: match.prefix,
      label: LABELS[key]};
  }

  function probableResult(record, token, cost) {
    return {source: record.source, sourceId: record.source.source_id || record.source.id,
      sourceLine: record.source.source_line, pageId: probablePageId(record, token),
      kind: "probable", side: "vlb", scope: "probable",
      queryPath: "orthography-model", matchedForm: token, cost, prefix: record.vlbTokens[0] === token,
      label: LABELS.probable};
  }

  function search(index, query, model, options = {}) {
    if (!index?.records || !index?.vlbTokenRecords) throw new TypeError("Índice de busca inválido.");
    const normalizedQuery = normalizeForm(query);
    const queryTokens = words(normalizedQuery);
    if (!queryTokens.length) return {query: normalizedQuery, results: [], total: 0, directTotal: 0, probableTotal: 0};
    const literal = [];
    const seen = new Set();
    for (const record of index.records) {
      const match = literalCandidate(record, queryTokens);
      if (!match) continue;
      const result = directResult(record, match, queryTokens);
      literal.push(result);
      seen.add(result.sourceId);
    }
    const scopeRank = {whole: 0, inside: 1};
    const sideRank = {vlb: 0, portuguese: 1, transcription: 2};
    literal.sort((left, right) => scopeRank[left.scope] - scopeRank[right.scope] ||
      Number(right.prefix) - Number(left.prefix) || sideRank[left.side] - sideRank[right.side] ||
      left.sourceLine - right.sourceLine || String(left.sourceId).localeCompare(String(right.sourceId)));

    const probable = [];
    const queryLength = graphemes(normalizedQuery).length;
    const threshold = Number(options.maxProbableCost ?? .15);
    if (model && queryLength >= Number(options.minProbableGraphemes ?? 3)) {
      const compiled = typeof model.score === "function" ? model : compileModel(model);
      for (const [token, records] of index.vlbTokenRecords) {
        if (token === normalizedQuery) continue;
        const targetLength = graphemes(token).length;
        if (Math.abs(queryLength - targetLength) > Math.ceil(Math.max(queryLength, targetLength) * .4)) continue;
        const cost = compiled.score(normalizedQuery, token);
        if (cost > threshold || cost <= 0) continue;
        for (const record of records) {
          const sourceId = record.source.source_id || record.source.id;
          if (seen.has(sourceId)) continue;
          const result = probableResult(record, token, cost);
          const existing = probable.findIndex(item => item.sourceId === sourceId);
          if (existing < 0) probable.push(result);
          else if (cost < probable[existing].cost ||
              (cost === probable[existing].cost && token.localeCompare(probable[existing].matchedForm) < 0)) probable[existing] = result;
        }
      }
    }
    probable.sort((left, right) => left.cost - right.cost || Number(right.prefix) - Number(left.prefix) ||
      left.sourceLine - right.sourceLine || left.matchedForm.localeCompare(right.matchedForm));
    const probableLimit = Math.max(0, Number(options.maxProbableResults ?? 40));
    const all = literal.concat(probable.slice(0, probableLimit));
    const limit = Math.max(1, Number(options.limit ?? 100));
    return {query: normalizedQuery, results: all.slice(0, limit), total: literal.length + probable.length,
      directTotal: literal.length, probableTotal: probable.length, probableShown: Math.min(probable.length, probableLimit)};
  }

  return {LABELS, normalizeForm, words, graphemes, splitRecord, compileModel, buildIndex, search};
});
