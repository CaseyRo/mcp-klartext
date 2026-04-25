"""End-to-end tests for the MCP tools via FastMCP's in-memory client."""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastmcp import Client

from mcp_klartext.server import mcp


def _payload(result: Any) -> dict:
    """Extract the JSON dict payload returned by a tool call."""
    if getattr(result, "data", None) is not None:
        return result.data
    if getattr(result, "structured_content", None):
        return result.structured_content
    # Fall back to parsing the first text content block.
    return json.loads(result.content[0].text)


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


async def test_list_tools_exposes_expected_surface(client: Client):
    tools = await client.list_tools()
    names = {t.name for t in tools}
    assert {
        "generate_text_context",
        "get_voice_dna",
        "get_brand_context",
        "list_platforms",
        "get_platform_template",
        "scan_draft",
        "portal_routing_guide",
    } <= names


async def test_scan_draft_flags_lexical_tell(client: Client):
    result = await client.call_tool(
        "scan_draft", {"text": "We delve into the robust landscape of tooling."}
    )
    payload = _payload(result)
    assert payload["clean"] is False
    patterns = {i["pattern"] for i in payload["issues"]}
    assert {"delve", "robust", "landscape of"} <= patterns


async def test_scan_draft_clean_draft(client: Client):
    text = "I learned to code on my dad's lap. The screen glowed green."
    result = await client.call_tool("scan_draft", {"text": text})
    payload = _payload(result)
    assert payload["clean"] is True
    assert payload["stats"]["high"] == 0


async def test_get_voice_dna_returns_dna(client: Client):
    result = await client.call_tool("get_voice_dna", {})
    payload = _payload(result)
    assert "voice_dna" in payload
    assert "## Voice DNA" in payload["voice_dna"]


async def test_list_platforms_returns_bundled(client: Client):
    result = await client.call_tool("list_platforms", {})
    payload = _payload(result)
    keys = {p["key"] for p in payload["platforms"]}
    assert "linkedin-post" in keys
    assert "blog" in keys


async def test_get_platform_template_known(client: Client):
    result = await client.call_tool(
        "get_platform_template", {"platform": "linkedin-post"}
    )
    payload = _payload(result)
    assert payload["platform"] == "linkedin-post"
    assert payload["template"]


async def test_get_platform_template_rejects_unknown_via_literal(client: Client):
    # The platform arg is a Literal — invalid values should raise rather than
    # hit the error-branch fallback in the tool body.
    with pytest.raises(Exception):
        await client.call_tool("get_platform_template", {"platform": "not-a-platform"})


async def test_get_brand_context_lists_brands_when_omitted(client: Client):
    result = await client.call_tool("get_brand_context", {})
    payload = _payload(result)
    keys = {b["key"] for b in payload["brands"]}
    # CDI-1041 — canonical bare slugs across the fleet.
    assert {"casey-berlin", "cdit-works", "storykeep", "nah", "yorizon"} <= keys


async def test_get_brand_context_canonical_key(client: Client):
    result = await client.call_tool("get_brand_context", {"context": "casey-berlin"})
    payload = _payload(result)
    assert payload["context"] == "casey-berlin"
    assert payload["rules"]


async def test_get_brand_context_legacy_dot_form_still_works(client: Client):
    # Legacy callers that still pass "casey.berlin" should resolve.
    result = await client.call_tool("get_brand_context", {"context": "casey.berlin"})
    payload = _payload(result)
    assert payload["context"] == "casey-berlin"
    assert payload["rules"]


async def test_get_brand_context_legacy_at_prefixed_works(client: Client):
    # Legacy bildsprache "@cdit" form should resolve to cdit-works.
    result = await client.call_tool("get_brand_context", {"context": "@cdit"})
    payload = _payload(result)
    assert payload["context"] == "cdit-works"


async def test_get_brand_context_unknown_key_returns_error(client: Client):
    result = await client.call_tool("get_brand_context", {"context": "@nope"})
    payload = _payload(result)
    assert "error" in payload
    assert "available" in payload


async def test_generate_text_context_merges_everything(client: Client):
    result = await client.call_tool(
        "generate_text_context",
        {"context": "casey-berlin", "platform": "blog", "language": "en"},
    )
    payload = _payload(result)
    assert "voice_dna" in payload
    assert payload["brand_context"]["name"] == "casey-berlin"
    assert payload["platform_template"]["name"] == "blog"
    assert payload["language"] == "en"


async def test_generate_text_context_hints_when_context_missing(client: Client):
    result = await client.call_tool("generate_text_context", {})
    payload = _payload(result)
    assert payload["brand_context"]["missing"] is True
    assert payload["platform_template"]["missing"] is True


async def test_portal_routing_guide_has_klartext_entry(client: Client):
    result = await client.call_tool("portal_routing_guide", {})
    payload = _payload(result)
    assert "klartext" in payload["servers"]
    assert payload["servers"]["klartext"]["domain"] == "content"
