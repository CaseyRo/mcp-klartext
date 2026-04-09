"""FastMCP server for brand-aware copywriting context."""

from __future__ import annotations

import logging
import os
from typing import Literal

from fastmcp import FastMCP
from mcp.types import Icon

from mcp_klartext.auth import BearerTokenVerifier
from mcp_klartext.config import settings
from mcp_klartext.platforms import load_platforms
from mcp_klartext.voice import load_voice_data

logger = logging.getLogger(__name__)

# Load all content at startup
voice_data = load_voice_data()
platform_data = load_platforms()

# Build authentication (bearer token via MCP_API_KEY)
_api_key = os.getenv("MCP_API_KEY", "")
_auth = BearerTokenVerifier(api_key=_api_key) if _api_key else None

mcp = FastMCP(
    "mcp-klartext",
    auth=_auth,
    icons=[
        Icon(
            src="data:image/png;base64,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",
            mimeType="image/png",
            sizes=["96x96"],
        ),
    ],
)


@mcp.tool
async def generate_text_context(
    context: str | None = None,
    platform: str | None = None,
    language: str | None = None,
) -> dict:
    """[content] Get complete writing context for brand-aware content generation.

    Returns voice DNA rules, brand-specific settings, platform template,
    bleed scan rules, and the Bildsprache handshake format — everything
    an LLM needs to generate content in Casey's voice.

    Prefer this single call over separate get_voice_dna + get_brand_context
    + get_platform_template calls — it returns all three in one response.

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
    """[content] Get Casey's voice DNA rules for content generation.

    Returns opening patterns, sentence architecture, signature moves,
    closing patterns, vocabulary use/avoid lists, trilingual workflow,
    and voice calibration protocol.
    """
    return {
        "voice_dna": voice_data.voice_dna,
    }


@mcp.tool
async def get_brand_context(context: str | None = None) -> dict:
    """[content] Get brand-specific voice, visual, and language settings.

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


@mcp.tool
async def get_platform_template(platform: Literal["linkedin-post", "linkedin-article", "blog", "newsletter", "reflection", "proposal", "instagram", "whatsapp"]) -> dict:
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


@mcp.tool
async def portal_routing_guide() -> dict:
    """[infra] Returns a routing guide mapping common intents to the correct upstream MCP server.

    Call this once per session to understand which server handles what.
    Use the domain tags in tool descriptions ([finance], [notes], etc.) for quick filtering.
    """
    return {
        "servers": {
            "lexoffice": {
                "domain": "finance",
                "intents": ["create invoice", "manage contacts (accounting)", "quotations", "expenses", "financial overview"],
            },
            "outbank": {
                "domain": "finance",
                "intents": ["search bank transactions", "aggregate spending", "budget analysis"],
            },
            "siyuan": {
                "domain": "notes",
                "intents": ["search notes", "create documents", "manage notebooks", "daily notes", "find tasks in notes"],
            },
            "apple-notes": {
                "domain": "notes",
                "intents": ["create Apple Notes", "create recipe notes"],
            },
            "things": {
                "domain": "tasks-gtd",
                "intents": ["capture tasks", "GTD workflow", "daily/weekly review", "project planning", "inbox processing"],
            },
            "zernio": {
                "domain": "social",
                "intents": ["social media posts", "schedule content", "analytics", "comments", "inbox/DMs", "manage accounts"],
            },
            "watermelon": {
                "domain": "crm",
                "intents": ["CRM contacts", "live-chat conversations", "send messages", "webhooks"],
            },
            "writings": {
                "domain": "content",
                "intents": ["create blog posts", "newsletters", "reflections", "publish content", "search writings"],
            },
            "klartext": {
                "domain": "content",
                "intents": ["brand voice context", "platform templates", "copywriting guidelines"],
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


def main() -> None:
    """Entry point for the mcp-klartext server."""
    if settings.transport == "http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
