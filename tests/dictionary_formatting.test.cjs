// Run from the repository root:
//   node --test tests/dictionary_formatting.test.cjs
//
// Execute the production dictionary formatter directly. No npm packages or
// hand-maintained copy of the formatting functions are involved.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const zlib = require('node:zlib');

const root = path.resolve(__dirname, '..');
const dictionaryScript = fs.readFileSync(path.join(root, 'js/index.js'), 'utf8');

const constantsStart = dictionaryScript.indexOf('  const TUPI_START_RE');
const constantsEnd = dictionaryScript.indexOf('  const SUBJ_PREF_MAP', constantsStart);
const formatterStart = dictionaryScript.indexOf('  function splitByBullet(');
const formatterEnd = dictionaryScript.indexOf('  function toggleContent(', formatterStart);
assert.ok(constantsStart >= 0 && constantsEnd > constantsStart);
assert.ok(formatterStart >= 0 && formatterEnd > formatterStart);

const formatVerbeteDefinition = vm.runInNewContext(`
  ${dictionaryScript.slice(constantsStart, constantsEnd)}
  const warnOnce = () => {};
  ${dictionaryScript.slice(formatterStart, formatterEnd)}
  formatVerbeteDefinition;
`, {
  window: { location: { pathname: '/nhe-enga/' } },
});

const compressedDictionary = fs.readFileSync(path.join(root, 'docs/dict-conjugated.json.gz'));
const dictionary = JSON.parse(zlib.gunzipSync(compressedDictionary));
const bibliographyIndex = dictionary.findIndex((record) => record.f === 'BIBLIOGRAFIA');
const lexicalDictionary = dictionary.slice(0, bibliographyIndex === -1 ? undefined : bibliographyIndex);

function classesFromTag(tag) {
  const match = tag.match(/\bclass=(['"])(.*?)\1/i);
  return new Set(match ? match[2].split(/\s+/).filter(Boolean) : []);
}

function hasClass(node, className) {
  return node.classes.has(className);
}

function ancestors(node) {
  const result = [];
  for (let current = node.parent; current; current = current.parent) {
    result.push(current);
  }
  return result;
}

function textContent(node) {
  return node.directText + node.children.map(textContent).join('');
}

// Keep this predicate independent from the formatter implementation while
// covering numeric, "p.", verso/recto, Roman-numeral, "cap.", and section locators.
const SOURCE_LOCATOR_TAIL_RE = /(?:^|[,;]\s*)(?:(?:(?:p\.\s*)?\d+(?:[vr])?|[IVXLCDM]+|cap\.\s*[IVXLCDMivxlcdm]+|§\s*\d+)(?:\s*[-–]\s*(?:\d+(?:[vr])?|[IVXLCDM]+))?(?:\s*,\s*\d{4})?(?:\s*[,;]\s*adapt\.)?|(?:in\s+)?Ar\.,\s*Cat)\]?\s*\.?$/;
const GENERATED_FORMATTER_TAG_RE = /<\/?(?:div|span|a)\b[^>]*>|<br\s*\/?\s*>/gi;
const GENERATED_CATEGORY_TOKENS = new Set([
  'adj', 'adv', 'adjetivo', 'advérbio',
]);

function lexicalTokens(value) {
  return (value.match(/[\p{L}\p{M}]+/gu) || [])
    .map((token) => token.normalize('NFC').toLowerCase())
    .filter((token) => !GENERATED_CATEGORY_TOKENS.has(token));
}

function missingLexicalTokens(source, formatted) {
  const visibleFormatted = formatted.replace(GENERATED_FORMATTER_TAG_RE, ' ');
  const available = new Map();
  lexicalTokens(visibleFormatted).forEach((token) => {
    available.set(token, (available.get(token) || 0) + 1);
  });
  const missing = [];
  lexicalTokens(source).forEach((token) => {
    const count = available.get(token) || 0;
    if (count) available.set(token, count - 1);
    else missing.push(token);
  });
  return missing;
}

function isSingleSourceCitation(text) {
  const plain = text.trim();
  if (!/^\([^()]+\)$/.test(plain)) return false;
  const inner = plain.slice(1, -1).trim();
  return inner.includes(',') && SOURCE_LOCATOR_TAIL_RE.test(inner);
}

function isSourceCitation(text) {
  const plain = text.trim();
  const citations = plain.match(/\([^()]+\)/g) || [];
  return Boolean(citations.length)
    && citations.every(isSingleSourceCitation)
    && citations.join(' ') === plain.replace(/\s+/g, ' ');
}

function parseGeneratedHtml(html) {
  const rootNode = {
    tagName: '#root', classes: new Set(), parent: null, children: [], directText: '',
  };
  const stack = [rootNode];
  const nodes = [];
  const errors = [];
  const tokens = html.match(/<\/?[A-Za-z][^>]*>|[^<]+|</g) || [];

  for (const token of tokens) {
    if (!token.startsWith('<') || !/^<\/?[A-Za-z]/.test(token)) {
      stack.at(-1).directText += token;
      continue;
    }

    const closing = token.startsWith('</');
    const nameMatch = token.match(/^<\/?([A-Za-z][A-Za-z0-9-]*)/);
    const tagName = nameMatch[1].toLowerCase();
    if (closing) {
      const current = stack.at(-1);
      if (current.tagName !== tagName) {
        errors.push(`closing </${tagName}> while <${current.tagName}> is open`);
      } else {
        stack.pop();
      }
      continue;
    }

    const parent = stack.at(-1);
    const node = {
      tagName,
      classes: classesFromTag(token),
      parent,
      children: [],
      directText: '',
    };
    parent.children.push(node);
    nodes.push(node);
    if (tagName !== 'br' && !token.endsWith('/>')) stack.push(node);
  }

  if (stack.length !== 1) {
    errors.push(`unclosed tags: ${stack.slice(1).map((node) => node.tagName).join(', ')}`);
  }
  return { rootNode, nodes, errors };
}

function validateFormattedDefinition(html) {
  const { nodes, errors } = parseGeneratedHtml(html);
  const violations = [...errors];
  const isQuoteLine = (node) => hasClass(node, 'quote-tupi') || hasClass(node, 'quote-pt');
  const isSemanticContainer = (node) => (
    hasClass(node, 'sense-section-title') || hasClass(node, 'sense-definition')
  );

  for (const node of nodes) {
    const parent = node.parent;
    const lineage = ancestors(node);

    if (hasClass(node, 'sense-quote')) {
      if (lineage.some(isSemanticContainer)) {
        violations.push('.sense-quote is nested in a title or definition');
      }
      if (node.directText.trim()) {
        violations.push(`text directly inside .sense-quote: ${JSON.stringify(node.directText.trim())}`);
      }
      for (const child of node.children) {
        const allowed = [
          'quote-tupi', 'quote-pt', 'quote-citation', 'dialogue-line',
        ].some((className) => hasClass(child, className));
        if (!allowed) {
          violations.push(`unexpected <${child.tagName}> directly inside .sense-quote`);
        }
      }
    }

    if (isQuoteLine(node)) {
      if (!parent || !hasClass(parent, 'sense-quote')) {
        violations.push(`.${[...node.classes].join('.')} is not a direct child of .sense-quote`);
      }
      const lineText = textContent(node).trim();
      if (!lineText) {
        violations.push(`empty .${[...node.classes].join('.')}`);
      }
      if (hasClass(node, 'quote-tupi') && /^\[\s*(?:adj|adv)\.?\s*:/i.test(lineText)) {
        violations.push(`bracketed category label is styled as Tupi: ${JSON.stringify(lineText)}`);
      }
      if (
        hasClass(node, 'quote-tupi')
        && /^(?:\[\s*(?:adj|adv|s|v)\b|\(\s*(?:adj|adv|s|v)\.)/i.test(lineText)
      ) {
        violations.push(`grammatical category label is styled as Tupi: ${JSON.stringify(lineText)}`);
      }
      if (hasClass(node, 'quote-tupi') && /^\s*[:]/.test(lineText)) {
        violations.push(`separator colon is stranded in Tupi: ${JSON.stringify(lineText)}`);
      }
      if (hasClass(node, 'quote-tupi') && /^\(ou\b/i.test(lineText)) {
        violations.push(`variant parenthesis is stranded in Tupi: ${JSON.stringify(lineText)}`);
      }
      if (hasClass(node, 'quote-tupi')) {
        const sourceCitation = [...lineText.matchAll(/\([^()]+\)/g)]
          .find((match) => isSingleSourceCitation(match[0]));
        if (sourceCitation) {
          violations.push(`source citation is stranded in Tupi: ${JSON.stringify(lineText)}`);
        }
      }
      if (
        hasClass(node, 'quote-tupi')
        && /^(?:\([^)]*\)\s*)?(?:o mesmo que|pode\b|faz\b)/i.test(lineText)
      ) {
        violations.push(`editorial prose is styled as Tupi: ${JSON.stringify(lineText)}`);
      }
      if (hasClass(node, 'quote-tupi') && lineText.startsWith(',')) {
        violations.push(`separator comma is stranded in Tupi: ${JSON.stringify(lineText)}`);
      }
      if (hasClass(node, 'quote-pt')) {
        const strandedCitation = [...node.directText.matchAll(/\([^()]+\)/g)].find((match) => (
          isSourceCitation(match[0])
          && node.directText.slice(match.index + match[0].length).trim()
        ));
        if (strandedCitation) {
          violations.push(`source citation is stranded in .quote-pt prose: ${JSON.stringify(node.directText.trim())}`);
        }
      }
    }

    if (isSemanticContainer(node) && lineage.some((ancestor) => hasClass(ancestor, 'sense-quote'))) {
      violations.push(`.${[...node.classes].join('.')} is nested in .sense-quote`);
    }

    if (hasClass(node, 'sense-definition') && !textContent(node).trim()) {
      violations.push('empty .sense-definition');
    }
    if (
      hasClass(node, 'sense-definition')
      && /^\s*[-–]\s+/.test(textContent(node))
    ) {
      violations.push(`separator dash starts .sense-definition: ${JSON.stringify(textContent(node).trim())}`);
    }

    if (hasClass(node, 'quote-citation') && !isSourceCitation(textContent(node))) {
      violations.push(`non-source text is styled as .quote-citation: ${JSON.stringify(textContent(node).trim())}`);
    }
  }

  return violations;
}

test('source-citation invariant accepts numeric and Roman locators but rejects prose notes', () => {
  for (const citation of [
    '(Ar., Cat., 57v)',
    '(Léry, Histoire, 343-344)',
    '(Léry, Histoire, cap. XIII)',
    '(Frei Vicente do Salvador, História do Brasil, IV, cap. xviii)',
    '(Figueira, Missão, in Varnhagen, Hist. [4ª ed., 1951, III, 176])',
    '(Valente, Cantigas, IV, in Ar., Cat)',
    '(Léry, Histoire [1580], p. 276)',
    '(Bettendorff [1699], p. 318)',
    '(Laet, Novus Orbis, Livro XV, cap. IX, §6)',
    "(D'Abbeville, Histoire, LI)",
    '(Anch., Arte, 49v) (Anch., Arte, 50)',
  ]) {
    assert.equal(isSourceCitation(citation), true, citation);
  }
  for (const note of [
    '(isto é, caí em teus costumes)',
    '(Com o permissivo, geralmente só se usa com a 1ª p.)',
    '(Pode também ser pluriforme regular, com forma absol. em t-)',
    '(algo, civil)',
  ]) {
    assert.equal(isSourceCitation(note), false, note);
  }
});

test('all served Tupi-Portuguese definitions produce structurally valid quote markup', () => {
  const failures = [];
  let formattedCount = 0;

  lexicalDictionary.forEach((record, sourceIndex) => {
    if (record.t !== 1 && record.t !== true) return;
    if (!record.f || !record.d) return;
    formattedCount += 1;
    const violations = validateFormattedDefinition(formatVerbeteDefinition(record.d));
    if (violations.length) {
      failures.push({
        sourceIndex,
        headword: record.f,
        optionalNumber: String(record.o || ''),
        violations,
      });
    }
  });

  assert.ok(formattedCount > 8_000, `expected the served lexical corpus, got ${formattedCount} records`);
  assert.equal(
    failures.length,
    0,
    [
      `${failures.length} formatted records violate structural invariants.`,
      ...failures.slice(0, 12).map((failure) => (
        `index ${failure.sourceIndex} ${failure.headword}${failure.optionalNumber}: ${failure.violations.join('; ')}`
      )),
      failures.length > 12 ? `...and ${failures.length - 12} more` : '',
    ].filter(Boolean).join('\n'),
  );
});

test('formatting preserves every source lexical token', () => {
  const failures = [];
  lexicalDictionary.forEach((record, sourceIndex) => {
    if (record.t !== 1 && record.t !== true) return;
    if (!record.f || !record.d) return;
    const missing = missingLexicalTokens(
      record.d,
      formatVerbeteDefinition(record.d),
    );
    if (missing.length) {
      failures.push({sourceIndex, headword: record.f, missing});
    }
  });
  assert.equal(
    failures.length,
    0,
    failures.slice(0, 12).map(({sourceIndex, headword, missing}) => (
      `index ${sourceIndex} ${headword}: missing ${JSON.stringify(missing)}`
    )).join('\n'),
  );
});
