"""Brand-slug normalisation (CDI-1041 cross-skill alignment).

Canonical form across the fleet (mcp-bildsprache, mcp-klartext, mcp-writings)
is the **bare hyphenated slug**: ``casey-berlin``, ``cdit-works``,
``storykeep``, ``nah``, ``yorizon``.

This repo's voice loader historically produced ``casey.berlin`` (dot) for
Casey and ``cdit-works`` (bare slug) for CDiT — inconsistent with itself
and with the other repos. The MCP tool surface accepts any variant; we
normalise at the lookup boundary.
"""

from __future__ import annotations

CANONICAL_BRANDS: tuple[str, ...] = (
    "casey-berlin",
    "cdit-works",
    "storykeep",
    "nah",
    "yorizon",
)

_ALIASES: dict[str, str] = {
    # Bildsprache historical (@-prefixed, dot-separated, abbreviated)
    "@casey.berlin": "casey-berlin",
    "casey.berlin": "casey-berlin",
    "@cdit": "cdit-works",
    "cdit": "cdit-works",
    "@cdit-works": "cdit-works",
    "@cdit.works": "cdit-works",
    "cdit-works.de": "cdit-works",
    "cdit.works": "cdit-works",
    "@storykeep": "storykeep",
    "@nah": "nah",
    "@yorizon": "yorizon",
    # Underscored variants
    "casey_berlin": "casey-berlin",
    "cdit_works": "cdit-works",
}


def normalize_brand(brand: str | None) -> str | None:
    """Return the canonical bare-hyphenated slug for any known variant.

    None passes through. Unknown strings pass through unchanged.
    """
    if not brand:
        return brand
    cleaned = brand.strip()
    if cleaned in CANONICAL_BRANDS:
        return cleaned
    if cleaned in _ALIASES:
        return _ALIASES[cleaned]
    relaxed = cleaned.lower().lstrip("@")
    for needle in (cleaned, relaxed, f"@{relaxed}"):
        if needle in _ALIASES:
            return _ALIASES[needle]
    if relaxed in CANONICAL_BRANDS:
        return relaxed
    return cleaned


def lookup_brand(
    brands: dict[str, object], context: str | None
) -> object | None:
    """Look up a brand entry from the voice_data.brands dict.

    Tries multiple variants so callers can pass canonical bare slugs OR any
    legacy variant. Returns ``None`` when no variant matches.
    """
    if not context:
        return None

    # Direct hit (covers both legacy "casey.berlin" and bare "cdit-works"
    # — whatever the loader put in the dict).
    direct = brands.get(context)
    if direct is not None:
        return direct

    canonical = normalize_brand(context)
    if not canonical:
        return None

    # Try the canonical form, then a few legacy fall-back keys we know the
    # voice loader has historically produced.
    candidates = [
        canonical,
        canonical.replace("-", "."),  # casey-berlin -> casey.berlin
        f"@{canonical}",
    ]
    for c in candidates:
        if c in brands:
            return brands[c]
    return None
