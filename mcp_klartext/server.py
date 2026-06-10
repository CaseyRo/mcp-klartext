"""FastMCP server for brand-aware copywriting context."""

from __future__ import annotations

import logging
from typing import Literal

from datetime import datetime, timezone

from fastmcp import Context, FastMCP
from mcp.types import Icon, ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_klartext import __version__
from mcp_klartext.auth import BearerTokenVerifier
from mcp_klartext.config import settings
from mcp_klartext.models import (
    BrandContextResult,
    CaptionResult,
    GenerateTextContextResult,
    PlatformListing,
    PlatformTemplateResult,
    ReadMoreResult,
    ScanResult,
    VoiceDnaResult,
)
from mcp_klartext.platforms import load_platforms
from mcp_klartext.brands import lookup_brand
from mcp_klartext.references import (
    parse_frontmatter,
    references_from_frontmatter,
    render_ai_caption,
    render_readmore as _render_readmore_block,
)
from mcp_klartext.scanner import scan_for_ai_tells
from mcp_klartext.voice import load_voice_data

# Brands that no longer exist as separate contexts (May 2026 collapse).
# Surface a clear migration error rather than 'unknown brand'.
_REMOVED_BRANDS: dict[str, str] = {
    "casey-berlin": (
        "Brand consolidated. Use brand='casey' with register='personal'."
    ),
    "casey.berlin": (
        "Brand consolidated. Use brand='casey' with register='personal'."
    ),
    "casey_berlin": (
        "Brand consolidated. Use brand='casey' with register='personal'."
    ),
    "cdit": (
        "Brand consolidated. Use brand='casey' with register='professional'."
    ),
    "cdit-works": (
        "Brand consolidated. Use brand='casey' with register='professional'."
    ),
    "cdit-works.de": (
        "Brand consolidated. Use brand='casey' with register='professional'."
    ),
    "cdit_works": (
        "Brand consolidated. Use brand='casey' with register='professional'."
    ),
    "cdit.works": (
        "Brand consolidated. Use brand='casey' with register='professional'."
    ),
    "storykeep": (
        "Brand removed. Author under brand='casey' with register='professional'."
    ),
    "nah": (
        "Brand removed. Author under brand='casey' with register='professional'."
    ),
}

_VALID_REGISTERS: tuple[str, ...] = ("personal", "professional")

logger = logging.getLogger(__name__)

# Load all content at startup
voice_data = load_voice_data()
platform_data = load_platforms()

# Bearer token auth via settings (fail-fast for HTTP mode handled in config.py).
_api_key = settings.mcp_api_key.get_secret_value()
_auth = BearerTokenVerifier(api_key=_api_key) if _api_key else None
_start_time = datetime.now(timezone.utc)

_INSTRUCTIONS = """\
Klartext serves brand-aware copywriting *context* for Casey's voice — it is
content-only. It does not generate or store text; it returns the markdown rules
(voice DNA, brand contexts, register overlays, platform templates, AI-tell scan
results) for the calling LLM to follow, then write the finished copy itself.

How to pick a tool:
- Generating new copy? Call `generate_text_context` ONCE — it merges voice DNA +
  brand rules + register overlay + platform template + scan rules in a single
  response. Prefer it over the three granular accessors.
- Need just one piece? Use `get_voice_dna`, `get_brand_context`, `list_platforms`,
  or `get_platform_template`.
- Finishing a draft? ALWAYS run `scan_draft` before emitting the final Output
  Format block. If `clean` is false, rewrite the flagged high/medium spans and
  re-scan until clean.
- Embedding a Bildsprache image or citing sources? Use `render_ai_image_caption`
  and `render_readmore` to stay inside the AI-transparency contract.

Brands (May 2026 collapse): only `casey` and `yorizon` are active. The `casey`
brand REQUIRES a register — `personal` (recognition / manifesto voice) or
`professional` (verification / workshop voice). Legacy keys (casey-berlin,
cdit-works, storykeep, nah, ...) return a migration error pointing at the right
casey+register combination. Yorizon does not use registers.

Reference data is also available without spending a tool call: read the
`klartext://brands`, `klartext://platforms`, `klartext://platforms/{platform}`,
`klartext://voice-dna`, and `klartext://brand-detection` resources. The
`draft_and_scan` prompt encodes the full generate → scan → fix → emit loop.
"""

mcp = FastMCP(
    "mcp-klartext",
    instructions=_INSTRUCTIONS,
    auth=_auth,
    icons=[
        Icon(
            src="data:image/png;base64,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",
            mimeType="image/png",
            sizes=["96x96"],
        ),
    ],
)


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Generate writing context (one-shot)",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def generate_text_context(
    context: str | None = None,
    platform: str | None = None,
    language: str | None = None,
    register: Literal["personal", "professional"] | None = None,
    references: list[dict] | None = None,
    ctx: Context | None = None,
) -> GenerateTextContextResult:
    """[content] Get complete writing context for brand-aware content generation.

    Returns voice DNA rules, brand-specific settings (with the appropriate
    register overlay merged in), platform template, bleed scan rules, and
    the Bildsprache handshake format — everything an LLM needs to generate
    content in Casey's voice.

    Prefer this single call over separate get_voice_dna + get_brand_context
    + get_platform_template calls — it returns all three in one response.

    Args:
        context: Brand context. Active brands (May 2026 collapse): ``casey``,
                 ``yorizon``. Legacy variants (``casey-berlin``, ``cdit-works``,
                 ``cdit-works.de``, ``storykeep``, ``nah``, ...) return a
                 migration error pointing at the correct ``casey`` + register
                 combination. If omitted, returns voice DNA without
                 brand-specific rules.
        platform: Target platform (linkedin-post, blog, newsletter, etc.).
                  If omitted, returns available platforms list.
        language: Target language (en, de, nl). Affects trilingual workflow rules.
        register: For ``brand='casey'`` only. ``personal`` (recognition,
                  manifesto-adjacent voice) or ``professional`` (verification,
                  workshop voice). Yorizon does not use registers.
        references: Optional list of source references the caller is drafting
                    against. Each entry: {type: "stolperstein"|"url"|"document",
                    id?, href?, sha256?, title?}. Klartext is stateless — it
                    echoes these back under `references_passthrough` so the
                    caller can persist them into the draft's frontmatter.
    """
    if ctx is not None:
        await ctx.info(
            "Merging voice DNA"
            + (f" + brand '{context}'" if context else "")
            + (f"/{register}" if register else "")
            + (f" + platform '{platform}'" if platform else "")
        )

    result: dict = {
        "voice_dna": voice_data.voice_dna,
        "brand_detection": voice_data.brand_detection,
    }

    if context:
        # Removed/consolidated brands → migration message instead of
        # "unknown brand context", so callers know how to fix themselves.
        cleaned = context.strip().lstrip("@").lower()
        if cleaned in _REMOVED_BRANDS:
            result["brand_context"] = {
                "error": _REMOVED_BRANDS[cleaned],
                "removed": cleaned,
                "active": ["casey", "yorizon"],
            }
        else:
            brand = lookup_brand(voice_data.brands, context)
            if brand:
                if register and brand.name != "casey":
                    result["brand_context"] = {
                        "error": (
                            f"Brand '{brand.name}' does not use registers. "
                            "Omit the register argument."
                        ),
                    }
                elif register and register not in _VALID_REGISTERS:
                    result["brand_context"] = {
                        "error": (
                            f"Unknown register '{register}'. "
                            f"Valid: {list(_VALID_REGISTERS)}"
                        ),
                    }
                else:
                    payload: dict = {
                        "name": brand.name,
                        "rules": brand.content,
                    }
                    if register and brand.registers.get(register):
                        payload["register"] = register
                        payload["register_overlay"] = brand.registers[register].content
                    elif brand.name == "casey" and not register:
                        payload["register_required"] = True
                        payload["register_options"] = list(_VALID_REGISTERS)
                        payload["hint"] = (
                            "Casey brand needs a register. Pass "
                            "register='personal' or register='professional', "
                            "or include @casey/personal or @casey/professional "
                            "in the prompt."
                        )
                    result["brand_context"] = payload
            else:
                result["brand_context"] = {
                    "error": f"Unknown brand context: {context}",
                    "available": list(voice_data.brands.keys()),
                }
    else:
        result["brand_context"] = {
            "missing": True,
            "hint": "No brand context specified. Available brands:",
            "available": [
                {
                    "key": k,
                    "name": v.name,
                    "registers": (
                        list(v.registers.keys()) if v.registers else None
                    ),
                }
                for k, v in voice_data.brands.items()
            ],
        }

    # Platform template
    if platform:
        tmpl = platform_data.get(platform)
        if tmpl:
            result["platform_template"] = {
                "name": tmpl.name,
                "template": tmpl.content,
            }
        else:
            result["platform_template"] = {
                "error": f"Unknown platform: {platform}",
                "available": list(platform_data.keys()),
            }
    else:
        result["platform_template"] = {
            "missing": True,
            "available": list(platform_data.keys()),
        }

    # Language hint
    if language:
        result["language"] = language

    # Reference pass-through — Klartext does not persist drafts; the caller
    # (Writings or orchestrator) is expected to write these into the draft's
    # frontmatter under `references` so klartext_scan_draft and
    # render_readmore can see them on the next pass.
    if references:
        result["references_passthrough"] = references

    if ctx is not None:
        await ctx.info("Writing context assembled. Run scan_draft before finalizing.")

    return result


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Get voice DNA",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def get_voice_dna() -> VoiceDnaResult:
    """[content] Get Casey's voice DNA rules for content generation.

    Returns opening patterns, sentence architecture, signature moves,
    closing patterns, vocabulary use/avoid lists, trilingual workflow,
    and voice calibration protocol.
    """
    return {
        "voice_dna": voice_data.voice_dna,
    }


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Get brand context",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def get_brand_context(
    context: str | None = None,
    register: Literal["personal", "professional"] | None = None,
) -> BrandContextResult:
    """[content] Get brand-specific voice, visual, and language settings.

    Active brands (May 2026 collapse): ``casey``, ``yorizon``.

    Args:
        context: Specific brand to retrieve. Active brands: ``casey``,
                 ``yorizon``. Legacy keys (``casey-berlin``, ``cdit-works``,
                 ``storykeep``, ``nah``, ...) return a migration error
                 pointing at the correct ``casey`` + register combination.
                 If omitted, returns all active brands.
        register: For ``brand='casey'`` only. ``personal`` or ``professional``.
                  When provided, the response includes the register overlay
                  alongside the shared brand rules.
    """
    if context:
        cleaned = context.strip().lstrip("@").lower()
        if cleaned in _REMOVED_BRANDS:
            return {
                "error": _REMOVED_BRANDS[cleaned],
                "removed": cleaned,
                "active": ["casey", "yorizon"],
            }
        brand = lookup_brand(voice_data.brands, context)
        if brand:
            if register and brand.name != "casey":
                return {
                    "error": (
                        f"Brand '{brand.name}' does not use registers. "
                        "Omit the register argument."
                    ),
                }
            if register and register not in _VALID_REGISTERS:
                return {
                    "error": (
                        f"Unknown register '{register}'. "
                        f"Valid: {list(_VALID_REGISTERS)}"
                    ),
                }
            payload: dict = {
                "context": brand.name,
                "rules": brand.content,
            }
            if brand.registers:
                payload["registers"] = list(brand.registers.keys())
            if register and brand.registers.get(register):
                payload["register"] = register
                payload["register_overlay"] = brand.registers[register].content
            return payload
        return {
            "error": f"Unknown brand context: {context}",
            "available": list(voice_data.brands.keys()),
        }

    return {
        "brands": [
            {
                "key": k,
                "name": v.name,
                "preview": v.content[:200],
                "registers": (
                    list(v.registers.keys()) if v.registers else None
                ),
            }
            for k, v in voice_data.brands.items()
        ],
    }


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="List platform templates",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def list_platforms() -> PlatformListing:
    """[content] List available platform templates with their key constraints."""
    return {
        "platforms": [
            {
                "key": k,
                "name": v.name,
                "summary": v.summary,
            }
            for k, v in platform_data.items()
        ],
    }


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Get platform template",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def get_platform_template(
    platform: Literal[
        "linkedin-post",
        "linkedin-article",
        "blog",
        "newsletter",
        "reflection",
        "proposal",
        "instagram",
        "whatsapp",
    ],
) -> PlatformTemplateResult:
    """[content] Get a specific platform's full template with structure and constraints.

    Args:
        platform: Platform name (linkedin-post, linkedin-article, blog,
                  newsletter, reflection, proposal, instagram, whatsapp).
    """
    tmpl = platform_data.get(platform)
    if tmpl:
        return {
            "platform": tmpl.name,
            "template": tmpl.content,
        }
    return {
        "error": f"Unknown platform: {platform}",
        "available": list(platform_data.keys()),
    }


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Scan draft for AI tells",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def scan_draft(
    text: str,
    brand: str | None = None,
    ctx: Context | None = None,
) -> ScanResult:
    """[content] Scan a draft for AI-tell patterns before finalizing it.

    Implements the AI Bleed Scan rubric (see voice DNA) programmatically.
    Run this after generating a draft and before emitting the final Output
    Format block. If `clean` is false, rewrite the flagged spans and re-scan.

    Args:
        text: The draft markdown to scan.
        brand: Optional brand context. When ``brand='casey'``, the May 2026
               hard rules apply (no em-dashes, no all-caps, anti-anchor
               proximity). Other brands run only the generic AI-tell checks.

    Returns:
        issues: list of {category, pattern, match, line, severity, suggestion}
        stats: {word_count, em_dash_count, em_dash_budget, high/medium/low counts}
        brand: the brand argument echoed back
        clean: true iff no high or medium severity hits
    """
    result = scan_for_ai_tells(text, brand=brand)
    if ctx is not None:
        stats = result["stats"]
        verdict = "clean" if result["clean"] else "needs rewrites"
        await ctx.info(
            f"Scan {verdict}: {stats['high']} high, {stats['medium']} medium, "
            f"{stats['low']} low across {stats['word_count']} words."
        )
    return result


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Render 'Read more' block",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def render_readmore(
    draft_markdown: str,
    language: Literal["de", "en", "nl"] = "en",
) -> ReadMoreResult:
    """[content] Render a 'Weiterlesen' / 'Read more' block from a draft's references.

    Stateless — parses the YAML frontmatter of the provided draft, looks for
    a `references: [...]` array, and returns the rendered block. Empty input
    returns an empty string.

    The caller is responsible for inserting the returned block into the draft
    before publishing (Klartext does not persist drafts).

    Args:
        draft_markdown: Full draft markdown including YAML frontmatter.
        language: Output language. "de" → "Weiterlesen", "en" → "Read more".

    Returns:
        {block: str, references: [...], language: str}
    """
    meta, _ = parse_frontmatter(draft_markdown)
    refs = references_from_frontmatter(meta)
    block = _render_readmore_block(refs, language=language)
    return {
        "block": block,
        "references": [
            {
                "type": r.type,
                "id": r.id,
                "href": r.href,
                "sha256": r.sha256,
                "title": r.title,
            }
            for r in refs
        ],
        "language": language,
    }


@mcp.tool(
    tags={"content"},
    annotations=ToolAnnotations(
        title="Render AI image caption",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def render_ai_image_caption(
    attribution: dict,
    language: Literal["de", "en", "nl"] = "en",
) -> CaptionResult:
    """[content] Render a figure caption from an ai_attribution payload.

    Produces a caption string combining (a) the author's `prompt_anchor` as a
    brief description and (b) a localised 'AI-generated with <provider>/<model>'
    attribution line. Use this when embedding Bildsprache images into Klartext
    drafts.

    Args:
        attribution: ai_attribution payload (v1) from Bildsprache.
        language: Output language.

    Returns:
        {caption: str}
    """
    return {"caption": render_ai_caption(attribution, language=language)}


@mcp.tool(
    tags={"infra"},
    annotations=ToolAnnotations(
        title="Portal routing guide",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def portal_routing_guide() -> dict:
    """[infra] Returns a routing guide mapping common intents to the correct upstream MCP server.

    Call this once per session to understand which server handles what.
    Use the domain tags in tool descriptions ([finance], [notes], etc.) for quick filtering.
    """
    return {
        "servers": {
            "lexoffice": {
                "domain": "finance",
                "intents": [
                    "create invoice",
                    "manage contacts (accounting)",
                    "quotations",
                    "expenses",
                    "financial overview",
                ],
            },
            "outbank": {
                "domain": "finance",
                "intents": [
                    "search bank transactions",
                    "aggregate spending",
                    "budget analysis",
                ],
            },
            "siyuan": {
                "domain": "notes",
                "intents": [
                    "search notes",
                    "create documents",
                    "manage notebooks",
                    "daily notes",
                    "find tasks in notes",
                ],
            },
            "apple-notes": {
                "domain": "notes",
                "intents": ["create Apple Notes", "create recipe notes"],
            },
            "things": {
                "domain": "tasks-gtd",
                "intents": [
                    "capture tasks",
                    "GTD workflow",
                    "daily/weekly review",
                    "project planning",
                    "inbox processing",
                ],
            },
            "zernio": {
                "domain": "social",
                "intents": [
                    "social media posts",
                    "schedule content",
                    "analytics",
                    "comments",
                    "inbox/DMs",
                    "manage accounts",
                ],
            },
            "watermelon": {
                "domain": "crm",
                "intents": [
                    "CRM contacts",
                    "live-chat conversations",
                    "send messages",
                    "webhooks",
                ],
            },
            "writings": {
                "domain": "content",
                "intents": [
                    "create blog posts",
                    "newsletters",
                    "reflections",
                    "publish content",
                    "search writings",
                ],
            },
            "klartext": {
                "domain": "content",
                "intents": [
                    "brand voice context",
                    "platform templates",
                    "copywriting guidelines",
                ],
            },
            "ytdlp": {
                "domain": "media",
                "intents": ["download videos", "convert video formats"],
            },
            "instaloader": {
                "domain": "media",
                "intents": ["fetch Instagram posts/reels"],
            },
            "read-website-fast": {
                "domain": "web",
                "intents": ["read web pages", "extract content as markdown"],
            },
        },
        "disambiguation": {
            "create contact": "For accounting → lexoffice. For CRM/chat → watermelon.",
            "search": "For notes → siyuan. For social → zernio. For blog content → writings.",
            "create note": "For Apple Notes → apple-notes. For blog drafts → writings.",
            "send message": "For live-chat → watermelon. For social DMs → zernio.",
        },
    }


# --------------------------------------------------------------------------- #
# Resources — reference data clients can pull without spending a tool call.
# Same content the tools return, addressable under the klartext:// scheme.
# --------------------------------------------------------------------------- #


@mcp.resource(
    "klartext://brands",
    name="Active brands",
    description="The active brand catalog (May 2026 collapse): casey + yorizon, with their registers.",
    mime_type="application/json",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def brands_resource() -> dict:
    """Active brand catalog with previews and available registers."""
    return {
        "brands": [
            {
                "key": k,
                "name": v.name,
                "preview": v.content[:200],
                "registers": list(v.registers.keys()) if v.registers else None,
            }
            for k, v in voice_data.brands.items()
        ],
        "registers": list(_VALID_REGISTERS),
    }


@mcp.resource(
    "klartext://brands/{brand}",
    name="Brand rules",
    description="Full voice/visual/language rules for a single active brand (casey | yorizon).",
    mime_type="application/json",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def brand_resource(brand: str) -> dict:
    """Full rules for one active brand, including any register overlays."""
    cleaned = brand.strip().lstrip("@").lower()
    if cleaned in _REMOVED_BRANDS:
        return {
            "error": _REMOVED_BRANDS[cleaned],
            "removed": cleaned,
            "active": ["casey", "yorizon"],
        }
    found = lookup_brand(voice_data.brands, brand)
    if found is None:
        return {
            "error": f"Unknown brand context: {brand}",
            "available": list(voice_data.brands.keys()),
        }
    payload: dict = {"name": found.name, "rules": found.content}
    if found.registers:
        payload["registers"] = {
            name: reg.content for name, reg in found.registers.items()
        }
    return payload


@mcp.resource(
    "klartext://platforms",
    name="Platform templates",
    description="All platform templates with their one-line constraints summary.",
    mime_type="application/json",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def platforms_resource() -> dict:
    """All platform keys with summaries."""
    return {
        "platforms": [
            {"key": k, "name": v.name, "summary": v.summary}
            for k, v in platform_data.items()
        ],
    }


@mcp.resource(
    "klartext://platforms/{platform}",
    name="Platform template",
    description="Full structure + constraints for a single platform template.",
    mime_type="application/json",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def platform_resource(platform: str) -> dict:
    """Full template for one platform."""
    tmpl = platform_data.get(platform)
    if tmpl is None:
        return {
            "error": f"Unknown platform: {platform}",
            "available": list(platform_data.keys()),
        }
    return {"platform": tmpl.name, "template": tmpl.content}


@mcp.resource(
    "klartext://voice-dna",
    name="Voice DNA",
    description="Casey's concatenated voice DNA rubric (DNA + trilingual + handshake + output + calibration + bleed scan).",
    mime_type="text/markdown",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def voice_dna_resource() -> str:
    """The full voice DNA markdown."""
    return voice_data.voice_dna


@mcp.resource(
    "klartext://brand-detection",
    name="Brand detection rules",
    description="Heuristics for inferring the intended brand/register from a prompt.",
    mime_type="text/markdown",
    tags={"content"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def brand_detection_resource() -> str:
    """The brand-detection markdown."""
    return voice_data.brand_detection


# --------------------------------------------------------------------------- #
# Prompts — guided workflows for the server's signature multi-step jobs.
# --------------------------------------------------------------------------- #


@mcp.prompt(
    name="draft_and_scan",
    description="Guided loop: generate in Casey's voice, scan for AI tells, fix, re-scan, emit the Output Format block.",
    tags={"content"},
)
def draft_and_scan_prompt(
    brief: str,
    brand: str = "casey",
    register: str = "professional",
    platform: str = "blog",
    language: str = "en",
) -> str:
    """Return the canonical draft → scan → fix → emit workflow as a prompt."""
    return (
        f"Write copy for this brief: {brief}\n\n"
        f"Brand: {brand}  Register: {register}  Platform: {platform}  "
        f"Language: {language}\n\n"
        "Follow this loop exactly:\n"
        "1. Call `generate_text_context` ONCE with the parameters above to load "
        "voice DNA + brand rules + register overlay + platform template. Do not "
        "call the granular accessors separately.\n"
        "2. Draft the copy strictly in that voice. Obey the casey hard rules "
        "(no em-dashes, no all-caps, anti-anchor proximity) when brand=casey.\n"
        "3. Call `scan_draft` with the draft text (and brand) before showing "
        "anything to the user.\n"
        "4. If `clean` is false, rewrite ONLY the flagged high/medium spans using "
        "each issue's `suggestion`, then call `scan_draft` again. Repeat until "
        "`clean` is true.\n"
        "5. If the draft cites sources or embeds Bildsprache images, call "
        "`render_readmore` and `render_ai_image_caption` and fold the results in.\n"
        "6. Emit the final copy inside the voice DNA's Output Format block.\n\n"
        "Return only the finished copy plus a one-line note of the final scan "
        "verdict."
    )


@mcp.prompt(
    name="brand_voice_brief",
    description="Load and summarise a brand+register's voice rules before writing, with the key do/don't list.",
    tags={"content"},
)
def brand_voice_brief_prompt(
    brand: str = "casey",
    register: str = "professional",
) -> str:
    """Return a prompt that loads and distils a brand/register voice brief."""
    return (
        f"Prepare to write as brand='{brand}'"
        + (f" register='{register}'" if brand == "casey" else "")
        + ".\n\n"
        "Steps:\n"
        "1. Read the `klartext://voice-dna` resource and the "
        f"`klartext://brands/{brand}` resource (use the matching register "
        "overlay for casey).\n"
        "2. Summarise, in <=10 bullets, the voice's signature moves, the "
        "vocabulary to use, and the vocabulary/patterns to avoid.\n"
        "3. State the hard rules that will be enforced by `scan_draft` so the "
        "first draft already complies.\n\n"
        "Output the brief only — do not write the copy yet."
    )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Public health endpoint. No upstream dependency — filesystem-backed."""
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-klartext",
        "version": __version__,
        "upstream_reachable": True,
        "uptime_seconds": int(
            (datetime.now(timezone.utc) - _start_time).total_seconds()
        ),
    })


@mcp.custom_route("/healthz", methods=["GET"])
async def health_check_z(request: Request) -> JSONResponse:
    return await health_check(request)


def main() -> None:
    """Entry point for the mcp-klartext server."""
    if settings.transport == "http":
        mcp.run(
            transport="streamable-http",
            host=settings.host,
            port=settings.port,
            stateless_http=True,
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
