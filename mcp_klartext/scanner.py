"""Scan drafts for AI-tell patterns.

Implements the AI Bleed Scan rubric from data/skill.md programmatically.
Returns structured issues the caller can act on, not a pass/fail verdict —
the LLM decides what to rewrite.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from mcp_klartext.references import (
    detect_image_embeds,
    has_readmore_heading,
    parse_frontmatter,
    references_from_frontmatter,
)

# High-severity single words. Word-boundary match, case-insensitive.
# Each entry is (pattern, human_label, suggestion).
LEXICAL_TELLS: list[tuple[str, str, str]] = [
    (
        r"\bdelve(?:s|d|ing)?\b",
        "delve",
        "Cut. Try 'look at', 'dig into', or just state the point.",
    ),
    (r"\bleverag(?:e|es|ed|ing)\b", "leverage", "Use 'use'. Almost always works."),
    (
        r"\bseamless(?:ly)?\b",
        "seamless",
        "Overused. Describe what actually happens instead.",
    ),
    (
        r"\brobust\b",
        "robust",
        "Say what you mean — 'reliable', 'handles edge cases', 'production-ready'.",
    ),
    (r"\bparadigm(?:\s+shift)?\b", "paradigm", "Drop it. Describe the actual change."),
    (r"\bfoster(?:s|ed|ing)?\b", "foster", "Try 'build', 'create', 'make room for'."),
    (r"\bembark(?:s|ed|ing)?\b", "embark", "Just say 'start' or 'begin'."),
    (r"\bharness(?:es|ed|ing)?\b", "harness", "Try 'use' or 'put to work'."),
    (r"\btapestry\b", "tapestry", "Almost never not-AI. Cut."),
    (r"\btestament\s+to\b", "testament to", "Cut. Show it instead of labeling it."),
    (
        r"\bat\s+the\s+intersection\s+of\b",
        "at the intersection of",
        "Overused. Name the two things and what's between them concretely.",
    ),
    (r"\brealm\s+of\b", "realm of", "Cut 'the realm of' — just say the thing."),
]

# Phrase-level patterns. Case-insensitive regex.
PHRASE_TELLS: list[tuple[str, str, str]] = [
    (
        r"it(?:'|\u2019)s\s+not\s+(?:just\s+)?[\w\s,]{1,40}?[—\-–]\s*it(?:'|\u2019)s\b",
        "it's not (just) X — it's Y",
        "Classic AI contrast. Kill it. State what it is, not what it isn't.",
    ),
    (
        r"\bnot\s+just\s+[\w\s]{1,30}?,\s*but\b",
        "not just X, but Y",
        "Same shape, different punctuation. Rewrite without the contrast.",
    ),
    (
        r"\bmore\s+than\s+just\b",
        "more than just",
        "Lazy amplifier. Describe what it actually is.",
    ),
    (
        r"\bbeyond\s+(?:the|just)\b",
        "beyond the/just",
        "AI connective tissue. Rewrite.",
    ),
    (
        r"\bin\s+(?:a\s+world\s+where|today(?:'|\u2019)s\s+fast-paced|an\s+era\s+of)\b",
        "'in a world where' / 'in today's fast-paced' / 'in an era of'",
        "Corporate-AI opener. Open with a scene, confession, or provocation.",
    ),
    (
        r"\blet(?:'|\u2019)s\s+dive\s+in\b",
        "let's dive in",
        "Cut. Start the thing instead of announcing it.",
    ),
    (
        r"\bimagine\s+a\s+world\b",
        "imagine a world",
        "AI-sermon opener. Try a concrete moment.",
    ),
    (
        r"\bit(?:'|\u2019)s\s+worth\s+noting\s+that\b",
        "it's worth noting that",
        "If it's worth noting, just note it.",
    ),
    (
        r"\bit\s+could\s+be\s+argued\s+that\b",
        "it could be argued that",
        "Argue it or cut it.",
    ),
    (
        r"\bnavigat(?:e|es|ed|ing)\s+the\s+\w+\b",
        "navigate the [abstract]",
        "'Navigating the landscape/complexity/world of X' — overused. Describe the specific action.",
    ),
    (
        r"\bunlock(?:s|ed|ing)?\s+(?:your|the|new)\b",
        "unlock (your|the|new)",
        "Cut. Say what actually changes.",
    ),
    (
        r"\blandscape\s+of\b",
        "landscape of",
        "AI metaphor. Name the space concretely.",
    ),
]


@dataclass
class Issue:
    category: str  # "lexical" | "phrase" | "structural" | "em_dash"
    pattern: str
    match: str
    line: int
    severity: str  # "high" | "medium" | "low"
    suggestion: str


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _find_em_dash_issues(text: str, word_count: int) -> tuple[list[Issue], int, int]:
    """Flag em-dash overuse. Budget: one per ~150 words, floor of 1."""
    em_dashes = [m for m in re.finditer(r"—", text)]
    budget = max(1, word_count // 150)
    count = len(em_dashes)
    issues: list[Issue] = []

    if count > budget:
        # Flag the dashes past the budget, not all of them.
        for m in em_dashes[budget:]:
            issues.append(
                Issue(
                    category="em_dash",
                    pattern=f"em-dash over budget (>{budget})",
                    match="—",
                    line=_line_number(text, m.start()),
                    severity="medium",
                    suggestion="Replace with period or colon. Em-dashes in every paragraph read as AI.",
                )
            )

    return issues, count, budget


def _find_lexical_issues(text: str) -> list[Issue]:
    issues: list[Issue] = []
    for pattern, label, suggestion in LEXICAL_TELLS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            issues.append(
                Issue(
                    category="lexical",
                    pattern=label,
                    match=m.group(0),
                    line=_line_number(text, m.start()),
                    severity="high",
                    suggestion=suggestion,
                )
            )
    return issues


def _find_phrase_issues(text: str) -> list[Issue]:
    issues: list[Issue] = []
    for pattern, label, suggestion in PHRASE_TELLS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            issues.append(
                Issue(
                    category="phrase",
                    pattern=label,
                    match=m.group(0).strip(),
                    line=_line_number(text, m.start()),
                    severity="high",
                    suggestion=suggestion,
                )
            )
    return issues


def _find_adjective_stacks(text: str) -> list[Issue]:
    """Three+ comma-separated adjectives before a noun = stack."""
    # Heuristic: word, word, (and )?word followed by a noun-ish word.
    # Keep it loose — false positives are fine for a low-severity check.
    issues: list[Issue] = []
    pattern = re.compile(
        r"\b(\w+ly|\w+ful|\w+ive|\w+ous|\w+ing|\w+ed|\w+al|\w+ic|\w+ble|\w+ant|\w+ent),\s+\w+,\s+(?:and\s+)?\w+\s+\w+",
    )
    for m in pattern.finditer(text):
        issues.append(
            Issue(
                category="structural",
                pattern="adjective stack",
                match=m.group(0),
                line=_line_number(text, m.start()),
                severity="low",
                suggestion="Trim to one adjective. Pick the one that does the most work.",
            )
        )
    return issues


def _find_repeated_sentence_openers(text: str) -> list[Issue]:
    """Three+ consecutive sentences starting with the same word."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    issues: list[Issue] = []
    if len(sentences) < 3:
        return issues

    run_start = 0
    for i in range(1, len(sentences)):
        prev_word = sentences[i - 1].split(" ", 1)[0].lower().strip(".,!?—:;")
        curr_word = sentences[i].split(" ", 1)[0].lower().strip(".,!?—:;")
        if prev_word and curr_word == prev_word:
            if i - run_start >= 2:  # 3+ consecutive = (i - run_start + 1) >= 3
                issues.append(
                    Issue(
                        category="structural",
                        pattern="repeated sentence opener",
                        match=curr_word,
                        line=1,  # approximate; we don't track sentence offsets here
                        severity="medium",
                        suggestion=f"Three+ sentences start with '{curr_word}'. Vary the openers.",
                    )
                )
                # Only flag the first hit per run.
                run_start = i + 1
        else:
            run_start = i

    return issues


def _find_attribution_issues(
    text: str, body: str, meta: dict
) -> tuple[list[Issue], dict]:
    """Flag missing Read more block and uncaptioned AI images.

    Returns (issues, diagnostics). Diagnostics is the attribution summary
    surfaced in the scan result for authors' pre-publish dashboard.
    """
    issues: list[Issue] = []

    refs = references_from_frontmatter(meta)
    readmore_rendered = has_readmore_heading(body)

    if refs and not readmore_rendered:
        # Warning severity — authors may deliberately omit the block.
        issues.append(
            Issue(
                category="attribution",
                pattern="NO_READMORE",
                match=f"{len(refs)} reference(s) in frontmatter, no Read more heading",
                line=1,
                severity="medium",  # warning-tier in our severity scheme
                suggestion=(
                    "Add a 'Read more' / 'Weiterlesen' section, or render it "
                    "programmatically via klartext_render_readmore."
                ),
            )
        )

    embeds = detect_image_embeds(body)
    ai_images = [e for e in embeds if e.is_bildsprache]
    captioned = [e for e in ai_images if e.has_ai_caption or _AI_CAPTION_MARKERS.search(e.alt)]

    for embed in ai_images:
        if embed.has_ai_caption or _AI_CAPTION_MARKERS.search(embed.alt):
            continue
        issues.append(
            Issue(
                category="attribution",
                pattern="UNCAPTIONED_AI_IMAGE",
                match=embed.src,
                line=embed.line,
                severity="high",  # error-tier — AI images must be labelled
                suggestion=(
                    "Add 'AI-generated' / 'KI-generiert' to the alt text or a "
                    "caption line adjacent to the image embed."
                ),
            )
        )

    diagnostics = {
        "ai_images_total": len(ai_images),
        "ai_images_captioned": len(captioned),
        "references_count": len(refs),
        "readmore_rendered": readmore_rendered,
    }
    return issues, diagnostics


# Re-export for _find_attribution_issues
_AI_CAPTION_MARKERS = re.compile(
    r"\b(?:ai[-\s]?generated|ki[-\s]?generiert|mit\s+ki|with\s+ai)\b", re.IGNORECASE
)


def scan_for_ai_tells(text: str) -> dict:
    """Run the AI Bleed Scan rubric on a draft.

    Returns a dict with issues, stats, and a `clean` boolean indicating
    whether the draft is free of high/medium severity hits.

    When the input has YAML frontmatter, the scan also runs attribution
    checks (NO_READMORE, UNCAPTIONED_AI_IMAGE) against the body, and the
    result includes an `attribution` diagnostics block.
    """
    meta, body = parse_frontmatter(text)
    # For all other checks we scan the full text; body-only for image detection.
    scannable = body if meta else text

    word_count = _word_count(scannable)

    em_dash_issues, em_dash_count, em_dash_budget = _find_em_dash_issues(
        scannable, word_count
    )
    lexical_issues = _find_lexical_issues(scannable)
    phrase_issues = _find_phrase_issues(scannable)
    structural_issues = _find_adjective_stacks(scannable) + _find_repeated_sentence_openers(
        scannable
    )
    attribution_issues, attribution_diagnostics = _find_attribution_issues(
        text, body if meta else text, meta
    )

    issues = (
        lexical_issues
        + phrase_issues
        + em_dash_issues
        + structural_issues
        + attribution_issues
    )
    issues.sort(key=lambda i: (i.line, i.category))

    blocking = [i for i in issues if i.severity in ("high", "medium")]

    return {
        "issues": [asdict(i) for i in issues],
        "stats": {
            "word_count": word_count,
            "em_dash_count": em_dash_count,
            "em_dash_budget": em_dash_budget,
            "issue_count": len(issues),
            "high": sum(1 for i in issues if i.severity == "high"),
            "medium": sum(1 for i in issues if i.severity == "medium"),
            "low": sum(1 for i in issues if i.severity == "low"),
        },
        "attribution": attribution_diagnostics,
        "clean": len(blocking) == 0,
    }
