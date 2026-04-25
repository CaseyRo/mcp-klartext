"""Reference surfacing: Read more blocks, AI image captions, frontmatter parsing.

Part of the cross-skill AI transparency contract (CDI-1014). Klartext is
stateless — it accepts draft markdown as input, parses the frontmatter,
and returns rendered blocks. Persistence lives in the caller (typically
Writings), not here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import yaml

# Hostname patterns that identify a Bildsprache-hosted image embedded in copy.
# Keep this list in sync with the Bildsprache hosting domains.
BILDSPRACHE_HOSTS = (
    "img.cdit-works.de",
    "img.casey.berlin",
    "img.storykeep.app",
    "img.nah.berlin",
)

# Case-insensitive AI-attribution markers accepted inside alt text / captions.
_AI_CAPTION_MARKERS = re.compile(
    r"\b(?:ai[-\s]?generated|ki[-\s]?generiert|mit\s+ki|with\s+ai)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Reference:
    type: str          # "stolperstein" | "url" | "document"
    id: str | None = None
    href: str | None = None
    sha256: str | None = None
    title: str | None = None


@dataclass(frozen=True)
class ImageEmbed:
    src: str
    alt: str
    line: int
    is_bildsprache: bool
    has_ai_caption: bool


_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from markdown body.

    Returns (metadata_dict, body_without_frontmatter). If no frontmatter is
    present, returns ({}, text). Malformed YAML raises yaml.YAMLError so the
    caller can surface a clear error to the author.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return {}, text
    raw_yaml = match.group(1)
    body = text[match.end():]
    data = yaml.safe_load(raw_yaml) or {}
    if not isinstance(data, dict):
        return {}, text
    return data, body


def references_from_frontmatter(meta: dict[str, Any]) -> list[Reference]:
    """Extract a typed Reference list from parsed frontmatter."""
    raw = meta.get("references")
    if not isinstance(raw, list):
        return []
    refs: list[Reference] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        t = entry.get("type")
        if t not in ("stolperstein", "url", "document"):
            continue
        refs.append(
            Reference(
                type=t,
                id=entry.get("id"),
                href=entry.get("href"),
                sha256=entry.get("sha256"),
                title=entry.get("title"),
            )
        )
    return refs


def render_readmore(references: list[Reference], language: str = "en") -> str:
    """Render a 'Read more' / 'Weiterlesen' block.

    Returns empty string when references is empty — never an empty heading.
    """
    if not references:
        return ""

    heading = {
        "de": "## Weiterlesen",
        "en": "## Read more",
        "nl": "## Lees verder",
    }.get(language, "## Read more")

    lines: list[str] = [heading, ""]
    for ref in references:
        lines.append(_render_reference_line(ref))
    return "\n".join(lines).rstrip() + "\n"


def _render_reference_line(ref: Reference) -> str:
    title = ref.title or _fallback_title(ref)
    if ref.type == "stolperstein":
        # Stolperstein internal link — placeholder scheme; callers can rewrite.
        href = f"stolperstein://{ref.id}" if ref.id else "stolperstein://"
        return f"- [{title}]({href})"
    if ref.type == "url":
        href = ref.href or ""
        return f"- [{title}]({href})"
    if ref.type == "document":
        # No link target — plain citation.
        return f"- {title}"
    return f"- {title}"


def _fallback_title(ref: Reference) -> str:
    if ref.type == "stolperstein":
        return ref.id or "Stolperstein entry"
    if ref.type == "url":
        if not ref.href:
            return "Untitled link"
        host = urlparse(ref.href).netloc
        return host or ref.href
    return "Document"


def render_ai_caption(attribution: dict[str, Any], language: str = "en") -> str:
    """Render a figure caption from an ai_attribution payload.

    Caption contains (a) author's prompt anchor as a brief description and
    (b) the attribution line localised for the draft's language.
    """
    anchor = (attribution or {}).get("prompt_anchor") or ""
    provider = (attribution or {}).get("provider") or "ai"
    model = (attribution or {}).get("model") or "unknown"
    attribution_line = {
        "de": f"KI-generiert mit {provider}/{model}",
        "en": f"AI-generated with {provider}/{model}",
        "nl": f"AI-gegenereerd met {provider}/{model}",
    }.get(language, f"AI-generated with {provider}/{model}")

    description = _shorten(anchor, limit=140)
    if description:
        return f"{description} — {attribution_line}"
    return attribution_line


def _shorten(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def detect_image_embeds(body: str) -> list[ImageEmbed]:
    """Find all markdown image embeds in the body and classify them.

    Classification: is the src on a Bildsprache-hosted domain, and does the
    alt text or the following line contain an AI-attribution marker?
    """
    results: list[ImageEmbed] = []
    for m in _IMAGE_RE.finditer(body):
        alt = m.group(1)
        src = m.group(2)
        line = body.count("\n", 0, m.start()) + 1

        # Look at alt + the line immediately after the embed (common caption
        # location) for AI attribution.
        following = body[m.end():].split("\n", 2)
        nearby = alt + " " + " ".join(following[:2])
        has_ai = bool(_AI_CAPTION_MARKERS.search(nearby))

        host = _safe_host(src)
        is_bildsprache = host in BILDSPRACHE_HOSTS

        results.append(
            ImageEmbed(
                src=src,
                alt=alt,
                line=line,
                is_bildsprache=is_bildsprache,
                has_ai_caption=has_ai,
            )
        )
    return results


def _safe_host(src: str) -> str:
    try:
        return urlparse(src).netloc
    except Exception:
        return ""


def has_readmore_heading(body: str, language: str = "en") -> bool:
    """Detect a 'Read more' / 'Weiterlesen' heading in the body."""
    # Language-agnostic — accept any of the supported headings regardless of
    # declared language, to be forgiving about multilingual drafts.
    pattern = re.compile(
        r"^#{1,4}\s+(?:Weiterlesen|Read\s+more|Lees\s+verder)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    return bool(pattern.search(body))
