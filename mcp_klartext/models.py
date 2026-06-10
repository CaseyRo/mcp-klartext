"""Pydantic output models for the Klartext tools.

These promote the previously-bare `dict` returns to typed models so FastMCP
advertises an `output_schema` for every tool. Every existing top-level field
is preserved — these models are an additive typing layer over the same
payloads, not a reshaping. Optional fields default to ``None`` and are excluded
from serialised output (``model_config`` below) so the error/migration branches
that historically returned a small dict keep producing the same compact JSON.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# NOTE ON RUNTIME SHAPE:
# These models are used as tool *return-type annotations* so FastMCP advertises
# a typed ``output_schema`` for every tool. The tool bodies still return the
# same compact, branch-specific dicts they always have (resolved / missing /
# error / migration). FastMCP serialises those dicts against the generated
# schema, emitting only the keys actually present — so error/migration branches
# stay compact (no wall of nulls) while clients still get the full contract.


class _Base(BaseModel):
    pass


# --------------------------------------------------------------------------- #
# Scan result (scan_draft)
# --------------------------------------------------------------------------- #


class ScanIssue(_Base):
    """A single AI-tell finding from the bleed scan."""

    category: str = Field(
        description="lexical | phrase | structural | em_dash | casey_rule | attribution",
    )
    pattern: str = Field(description="Human label / rule id for the matched tell.")
    match: str = Field(description="The exact span of text that matched.")
    line: int = Field(description="1-based line number of the match.")
    severity: str = Field(description="high | medium | low.")
    suggestion: str = Field(description="Concrete rewrite guidance for this hit.")


class ScanStats(_Base):
    """Aggregate counts for a scan run."""

    word_count: int
    em_dash_count: int
    em_dash_budget: int
    issue_count: int
    high: int
    medium: int
    low: int


class ScanAttribution(_Base):
    """AI-transparency diagnostics surfaced for the pre-publish dashboard."""

    ai_images_total: int
    ai_images_captioned: int
    references_count: int
    readmore_rendered: bool


class ScanResult(_Base):
    """Result of the AI Bleed Scan. ``clean`` is true iff no high/medium hits."""

    issues: list[ScanIssue]
    stats: ScanStats
    attribution: ScanAttribution
    brand: str | None = None
    clean: bool


# --------------------------------------------------------------------------- #
# Brand context (get_brand_context / generate_text_context.brand_context)
# --------------------------------------------------------------------------- #


class BrandSummary(_Base):
    """A brand entry in the catalog listing (get_brand_context with no context)."""

    key: str
    name: str
    preview: str | None = None
    registers: list[str] | None = None


class BrandContextResult(_Base):
    """get_brand_context result.

    Three mutually-exclusive branches share this model so clients get one
    schema for the whole tool:
    - single brand: ``context`` + ``rules`` (+ ``registers`` / ``register`` /
      ``register_overlay`` for casey);
    - listing (no context arg): ``brands``;
    - error / migration: ``error`` (+ ``removed`` / ``active`` / ``available``).
    """

    context: str | None = None
    rules: str | None = None
    registers: list[str] | None = None
    # ``register`` collides with ABCMeta.register on the BaseModel metaclass;
    # alias the Python attribute so the JSON/schema key stays ``register``.
    register_: str | None = Field(default=None, alias="register")
    register_overlay: str | None = None
    # Listing branch (no context arg):
    brands: list[BrandSummary] | None = None
    # Error / migration branches:
    error: str | None = None
    removed: str | None = None
    active: list[str] | None = None
    available: list[str] | None = None


# --------------------------------------------------------------------------- #
# Voice DNA (get_voice_dna)
# --------------------------------------------------------------------------- #


class VoiceDnaResult(_Base):
    """Casey's concatenated voice DNA rules."""

    voice_dna: str


# --------------------------------------------------------------------------- #
# Platforms (list_platforms / get_platform_template)
# --------------------------------------------------------------------------- #


class PlatformSummary(_Base):
    """A platform entry in the listing."""

    key: str
    name: str
    summary: str


class PlatformListing(_Base):
    """All available platform templates."""

    platforms: list[PlatformSummary]


class PlatformTemplateResult(_Base):
    """A single platform's full template."""

    platform: str | None = None
    template: str | None = None
    error: str | None = None
    available: list[str] | None = None


# --------------------------------------------------------------------------- #
# generate_text_context (one-shot merge)
# --------------------------------------------------------------------------- #


class GenerateTextContextResult(_Base):
    """One-shot writing context: voice + brand + platform + references.

    ``brand_context`` and ``platform_template`` are intentionally left as open
    dicts because each carries several mutually-exclusive shapes (resolved /
    missing / error / migration) that the caller already branches on by key.
    The wrapper schema still advertises the stable top-level keys.
    """

    voice_dna: str
    brand_detection: str
    brand_context: dict
    platform_template: dict
    language: str | None = None
    references_passthrough: list[dict] | None = None


# --------------------------------------------------------------------------- #
# References / captions (render_readmore / render_ai_image_caption)
# --------------------------------------------------------------------------- #


class ReferenceModel(_Base):
    """A typed source reference echoed back from a draft's frontmatter."""

    type: str
    id: str | None = None
    href: str | None = None
    sha256: str | None = None
    title: str | None = None


class ReadMoreResult(_Base):
    """Rendered 'Read more' / 'Weiterlesen' block plus the parsed references."""

    block: str
    references: list[ReferenceModel]
    language: str


class CaptionResult(_Base):
    """A rendered figure caption with localised AI attribution."""

    caption: str
