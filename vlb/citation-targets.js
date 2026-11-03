/* Choose a review navigation target; this never accepts a lexical association. */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.VLBCitationTargets = api;
})(typeof window === "object" ? window : null, function () {
  "use strict";

  const FORM = new Set(["loose_headword_form_key", "possible_prefixed_form_key"]);
  const HEAD = "context_to_Portuguese_head_token_overlap";
  const COMMON = new Set("que com por ser ter uma uns das dos nos vos lhe seu sua ela ele sem mais muito como quando onde para pelo pela todo toda aqui ali deste dessa isto act neut vel etc".split(" ").map(loose));
  const features = new WeakMap();

  function words(text) {
    return String(text || "").normalize("NFC").match(/\p{L}[\p{L}\p{M}]*(?:['’ʼ-]\p{L}[\p{L}\p{M}]*)*/gu) || [];
  }

  function literal(text) {
    return String(text || "").toLocaleLowerCase("pt-BR").normalize("NFD")
      .replace(/\p{M}/gu, "").replace(/['’ʼ‘]/g, "");
  }

  function loose(text) {
    // These aliases reproduce the existing retrieval keys, not a claim about
    // historical orthography, morphology, or equivalence between dictionary senses.
    return literal(String(text || "").toLocaleLowerCase("pt-BR").replace(/ç/g, "s"))
      .replace(/c/g, "k").replace(/j/g, "i").replace(/[^a-z]/g, "");
  }

  function evidence(association) {
    return new Set((association.evidence || []).map(item => item.type));
  }

  function pageFeatures(page) {
    if (features.has(page)) return features.get(page);
    const fragments = new Map((page.fragments || []).map(fragment => [fragment.id, fragment]));
    const lines = new Map((page.ocr_lines || []).map(line => [line.id, line]));
    const sourceKeys = new Map([...fragments].map(([id, fragment]) => [id, new Set(words(fragment.text).map(loose))]));
    const lineKeys = new Map([...lines].map(([id, line]) => [id, new Set(words(line.text).map(loose))]));
    const value = {fragments, lines, sourceKeys, lineKeys};
    features.set(page, value);
    return value;
  }

  function overlaps(keys, wanted) {
    return [...wanted].some(key => keys.has(key));
  }

  function validLineIds(fragment, lines) {
    if (fragment?.ocr?.status !== "aligned") return [];
    return [...new Set(fragment.ocr.line_ids || [])].filter(id => {
      const box = lines.get(id)?.box;
      return Array.isArray(box) && box.length === 4 && box.every(Number.isFinite) &&
        box[0] >= 0 && box[1] >= 0 && box[2] <= 1 && box[3] <= 1 &&
        box[0] < box[2] && box[1] < box[3];
    });
  }

  function fail(status, reason) {
    return {status, reason};
  }

  function choose(citation, page) {
    if (!citation || !page) return fail("unavailable", "missing_citation_or_page");
    const associations = citation.associations || [];
    const reviewed = associations.filter(association => association.status === "reviewed");
    const data = pageFeatures(page);

    if (reviewed.length) {
      const ids = new Set(reviewed.map(association => association.source_id));
      if (ids.size !== 1) return fail("ambiguous", "multiple_reviewed_sources");
      const association = reviewed[0];
      const fragment = data.fragments.get(association.source_id);
      const lineIds = validLineIds(fragment, data.lines);
      if (!lineIds.length) return fail("unavailable", "reviewed_source_without_aligned_ocr");
      const form = literal(association.source_form);
      const exact = form ? lineIds.filter(id => words(data.lines.get(id).text).some(word => literal(word) === form)) : [];
      return {status: "reviewed", source_id: fragment.id, line_ids: exact.length ? exact : lineIds,
        source_form: association.source_form || null, scope: exact.length ? "form" : "fragment",
        mechanism: "reviewed_association", reason: exact.length ? "reviewed_form_in_ocr" : "reviewed_fragment_ocr"};
    }

    const proposed = associations.filter(association => association.status === "proposed");
    if (!proposed.length) return fail("unavailable", "no_association");
    if (proposed.some(association => !Number.isFinite(association.score))) return fail("unavailable", "missing_retrieval_ranking");
    const ranked = [...proposed].sort((a, b) => b.score - a.score);
    if (ranked.length > 1 && ranked[0].score === ranked[1].score) return fail("ambiguous", "tied_candidates");
    const formCandidates = proposed.filter(association => [...evidence(association)].some(type => FORM.has(type)));
    if (!formCandidates.length) return fail("unavailable", "no_form_evidence");
    if (formCandidates.length > 1) return fail("ambiguous", "multiple_form_candidates");
    const association = formCandidates[0];
    if (association !== ranked[0]) return fail("ambiguous", "competing_stronger_candidate");
    const fragment = data.fragments.get(association.source_id);
    const lineIds = validLineIds(fragment, data.lines);
    if (!lineIds.length) return fail("unavailable", "source_without_aligned_ocr");

    const types = evidence(association);
    const key = loose(citation.headword);
    if (key.length < 3) return fail("unavailable", "short_form_alias");
    const keys = new Set(types.has("loose_headword_form_key") ? [key] : []);
    if (types.has("possible_prefixed_form_key")) ["a", "ai", "xe"].forEach(prefix => keys.add(prefix + key));
    const matchedForms = [...new Set(words(fragment.text).filter(word => keys.has(loose(word))))];
    if (!matchedForms.length) return fail("unavailable", "form_not_in_this_fragment");

    // The candidate list retains only its best few retrieval hits. Checking the
    // full page prevents another occurrence dropped from that list being hidden.
    const owners = [...data.sourceKeys].filter(([, sourceKeys]) => overlaps(sourceKeys, keys));
    if (owners.length !== 1 || owners[0][0] !== fragment.id) return fail("ambiguous", "form_repeated_in_page");
    const allowed = new Set(lineIds);
    const hits = [...data.lineKeys].filter(([, lineKeys]) => overlaps(lineKeys, keys)).map(([id]) => id);
    if (hits.some(id => !allowed.has(id))) return fail("ambiguous", "ocr_form_outside_fragment");

    const contextSupported = types.has(HEAD);
    if (!contextSupported && (key.length < 4 || COMMON.has(key))) return fail("unavailable", "short_or_common_ocr_only_alias");
    if (!contextSupported && !hits.length) return fail("unavailable", "insufficient_form_and_context_evidence");
    // No score cutoff is interpreted as a probability. A proposed jump requires
    // independent form/context or form/OCR evidence; its review status is unchanged.
    return {status: "proposed", source_id: fragment.id, line_ids: hits.length ? hits : lineIds,
      matched_forms: matchedForms, scope: hits.length ? "form" : "fragment",
      mechanism: contextSupported ? "form_and_context" : "form_in_ocr",
      reason: hits.length ? "unique_form_in_ocr" : "unique_form_and_context_fragment"};
  }

  return {choose};
});
