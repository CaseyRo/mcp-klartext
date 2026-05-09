"""Brand-slug normalisation.

Active brands (May 2026 brand collapse): ``casey`` and ``yorizon``. The
former ``casey-berlin``, ``cdit-works``, ``storykeep``, and ``nah`` keys
are no longer separate brands. Callers that pass legacy keys are routed
to the migration error in ``server.py`` (``_REMOVED_BRANDS``) — this
module's normalise/lookup paths only resolve the active brands.

The MCP tool surface accepts a few alias forms (`@casey`, `@yorizon`);
unknown strings pass through unchanged so the upstream layer can decide
whether to error or apply a removed-brand migration message.
"""

from __future__ import annotations

CANONICAL_BRANDS: tuple[str, ...] = (
    "casey",
    "yorizon",
)

_ALIASES: dict[str, str] = {
    "@casey": "casey",
    "@yorizon": "yorizon",
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
