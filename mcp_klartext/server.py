"""FastMCP server for brand-aware copywriting context."""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from mcp_klartext.auth import create_auth
from mcp_klartext.config import settings
from mcp_klartext.platforms import load_platforms
from mcp_klartext.voice import load_voice_data

logger = logging.getLogger(__name__)

# Load all content at startup
voice_data = load_voice_data()
platform_data = load_platforms()


def _build_auth():
    """Build auth provider if running in HTTP mode."""
    if settings.transport != "http":
        return None
    if not settings.keycloak_client_secret:
        logger.warning(
            "KEYCLOAK_CLIENT_SECRET not set — running without auth"
        )
        return None
    api_key = settings.ensure_api_key()
    return create_auth(
        api_key=api_key,
        base_url=settings.base_url,
        keycloak_issuer=settings.keycloak_issuer,
        keycloak_client_id=settings.keycloak_client_id,
        keycloak_client_secret=settings.keycloak_client_secret,
    )


mcp = FastMCP("mcp-klartext", auth=_build_auth())


@mcp.tool
async def generate_text_context(
    context: str | None = None,
    platform: str | None = None,
    language: str | None = None,
) -> dict:
    """Get complete writing context for brand-aware content generation.

    Returns voice DNA rules, brand-specific settings, platform template,
    bleed scan rules, and the Bildsprache handshake format — everything
    an LLM needs to generate content in Casey's voice.

    Args:
        context: Brand context (@casey.berlin, @cdit-works, @storykeep, @nah, @yorizon).
                 If omitted, returns voice DNA without brand-specific rules.
        platform: Target platform (linkedin-post, blog, newsletter, etc.).
                  If omitted, returns available platforms list.
        language: Target language (en, de, nl). Affects trilingual workflow rules.
    """
    result: dict = {
        "voice_dna": voice_data.voice_dna,
        "brand_detection": voice_data.brand_detection,
    }

    # Brand context
    if context:
        brand = voice_data.brands.get(context)
        if brand:
            result["brand_context"] = {
                "name": brand.name,
                "rules": brand.content,
            }
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
                {"key": k, "name": v.name}
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

    return result


@mcp.tool
async def get_voice_dna() -> dict:
    """Get Casey's voice DNA rules for content generation.

    Returns opening patterns, sentence architecture, signature moves,
    closing patterns, vocabulary use/avoid lists, trilingual workflow,
    and voice calibration protocol.
    """
    return {
        "voice_dna": voice_data.voice_dna,
    }


@mcp.tool
async def get_brand_context(context: str | None = None) -> dict:
    """Get brand-specific voice, visual, and language settings.

    Args:
        context: Specific brand to retrieve (@casey.berlin, @cdit-works,
                 @storykeep, @nah, @yorizon). If omitted, returns all brands.
    """
    if context:
        brand = voice_data.brands.get(context)
        if brand:
            return {
                "context": brand.name,
                "rules": brand.content,
            }
        return {
            "error": f"Unknown brand context: {context}",
            "available": list(voice_data.brands.keys()),
        }

    return {
        "brands": [
            {"key": k, "name": v.name, "preview": v.content[:200]}
            for k, v in voice_data.brands.items()
        ],
    }


@mcp.tool
async def list_platforms() -> dict:
    """List available platform templates with their key constraints."""
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


@mcp.tool
async def get_platform_template(platform: str) -> dict:
    """Get a specific platform's full template with structure and constraints.

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


def main() -> None:
    """Entry point for the mcp-klartext server."""
    if settings.transport == "http":
        mcp.run(transport="http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
