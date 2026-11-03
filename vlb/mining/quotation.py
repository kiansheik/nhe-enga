"""Literal dictionary example boundaries, with uncertainty kept as data.

This is an editorial-structure parser, not a language classifier. It recognizes
examples before translation dashes, preserves offsets, and never rewrites an
example to remove its optional arguments or create an unattested spelling.
"""
from __future__ import annotations

import re


def _top_level(text):
    """Tolerate leading closing reference punctuation in citation-local slices."""
    depth = 0
    result = []
    for char in text:
        result.append(depth == 0)
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
    return result


def parse_quotations(context):
    top = _top_level(context)
    quotes, issues, separators = [], [], []

    def add(left, right, kind, optional=()):
        while left < right and context[left] in " \t\n.;:?!…":
            left += 1
        while right > left and context[right - 1] in " \t\n.;:?!…":
            right -= 1
        if left == right:
            return
        if any(q["context_start"] == left and q["context_end"] == right for q in quotes):
            return
        quotes.append({"text": context[left:right], "context_start": left,
                       "context_end": right, "kind": kind,
                       "optional_intervals": [list(pair) for pair in optional
                                              if left <= pair[0] < pair[1] <= right]})

    for match in re.finditer(r"\s[-–—]\s", context):
        if not top[match.start()]:
            boundaries = [i for i in range(match.start()) if top[i] and context[i] in ":;●"]
            left = boundaries[-1] + 1 if boundaries else 0
            while left < match.start() and context[left] in " \t\n);]":
                left += 1
            # A translation separator trapped inside an unclosed example
            # bracket must not disappear as though no example were present.
            if left < match.start() and context[left] not in "([":
                issues.append({"reason": "nested_or_unclosed_example_separator",
                               "context_start": left, "context_end": match.start(),
                               "text": context[left:match.start()]})
            continue
        separators.append(match.start())
        boundaries = [i for i in range(match.start())
                      if top[i] and context[i] in ":;●"]
        left = boundaries[-1] + 1 if boundaries else 0
        right = match.start()
        while left < right and context[left] in " \t\n);]":
            left += 1
        # A dictionary's initial '(s.) -' / '(v.tr.) -' is not an example.
        while left < right and context[left] in "([":
            closing = ")" if context[left] == "(" else "]"
            end = context.find(closing, left + 1, right)
            if end < 0:
                break
            left = end + 1
            while left < right and context[left].isspace():
                left += 1
        if left >= right:
            continue
        # Keep the last sentence in a local entry segment, outside parentheses.
        cuts = [cut.end() for cut in re.finditer(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÎÔÛÃẼĨÕŨ])", context[left:right])
                if top[left + cut.start()]]
        if cuts:
            left += cuts[-1]
        tail = context[left:right].strip()
        if not tail:
            continue
        if len(tail) > 320:
            issues.append({"reason": "example_segment_too_long", "context_start": left,
                           "context_end": right, "text": context[left:right]})
            continue
        fragment_top = _top_level(context[left:right])
        parens = list(re.finditer(r"\([^()]*\)", context[left:right]))
        optional = []
        alternatives = []
        for paren in parens:
            a, b = left + paren.start(), left + paren.end()
            inner = context[a + 1:b - 1]
            alternative = re.match(r"\s*(?:ou|var\.?|também|tambem)\s+", inner, re.I)
            if alternative:
                alternatives.append((a, b, a + 1 + alternative.end(), b - 1))
            else:
                optional.append((a, b))
        remainder = re.sub(r"\([^()]*\)", "", context[left:right])
        if "(" in remainder or ")" in remainder or "[" in remainder or "]" in remainder:
            issues.append({"reason": "unparsed_example_brackets", "context_start": left,
                           "context_end": right, "text": context[left:right]})
        if alternatives:
            # Literal slices only. Shared material is not silently reassembled.
            first = alternatives[0][0]
            add(left, first, "literal_primary_before_parenthesized_alternative", optional)
            for a, b, begin, end in alternatives:
                add(begin, end, "literal_parenthesized_alternative")
                if context[b:right].strip(" .?!…"):
                    issues.append({"reason": "alternative_shared_tail_requires_review",
                                   "context_start": b, "context_end": right,
                                   "text": context[b:right]})
        else:
            # Slash-separated editorial alternatives are each retained verbatim.
            breaks = [left + i for i, char in enumerate(context[left:right])
                      if char == "/" and fragment_top[i]]
            bounds = [left] + [i + 1 for i in breaks]
            ends = breaks + [right]
            for begin, end in zip(bounds, ends):
                add(begin, end, "editorial_translation_separator_v2", optional)
    return {"version": "literal-example-parser-v2", "quotes": quotes,
            "issues": issues, "translation_separator_count": len(separators),
            "status": "partial" if issues else "parsed" if quotes else "no_example_detected",
            "is_language_annotation": False}
