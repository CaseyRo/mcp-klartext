"""Tests for the fastmcp uplift: annotations, structured output, resources, prompts.

These assert the additive MCP surface (typed output schemas, read-only hints,
klartext:// resources, guided prompts) without changing any existing tool
behaviour — the legacy shape assertions live in test_server.py / test_registers.py.
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from mcp_klartext.server import mcp

_ALL_TOOLS = {
    "generate_text_context",
    "get_voice_dna",
    "get_brand_context",
    "list_platforms",
    "get_platform_template",
    "scan_draft",
    "render_readmore",
    "render_ai_image_caption",
    "portal_routing_guide",
}


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


async def test_every_tool_has_title_and_readonly_hint(client: Client):
    tools = {t.name: t for t in await client.list_tools()}
    assert _ALL_TOOLS <= set(tools)
    for name in _ALL_TOOLS:
        ann = tools[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.title, f"{name} missing title"
        # Every tool here is a pure read / stateless render.
        assert ann.readOnlyHint is True, f"{name} not marked readOnlyHint"
        assert ann.idempotentHint is True, f"{name} not marked idempotentHint"


async def test_open_world_hints(client: Client):
    tools = {t.name: t for t in await client.list_tools()}
    # Content tools are closed-world (bundled data only).
    assert tools["scan_draft"].annotations.openWorldHint is False
    assert tools["get_voice_dna"].annotations.openWorldHint is False
    # The portal guide describes external sibling servers → open world.
    assert tools["portal_routing_guide"].annotations.openWorldHint is True


async def test_every_tool_advertises_output_schema(client: Client):
    for t in await client.list_tools():
        if t.name in _ALL_TOOLS:
            assert t.outputSchema, f"{t.name} has no output schema"


async def test_scan_draft_output_schema_shape(client: Client):
    tools = {t.name: t for t in await client.list_tools()}
    schema = tools["scan_draft"].outputSchema
    props = schema.get("properties", {})
    assert {"issues", "stats", "attribution", "brand", "clean"} <= set(props)


async def test_brand_context_schema_keeps_register_key(client: Client):
    tools = {t.name: t for t in await client.list_tools()}
    schema = tools["get_brand_context"].outputSchema
    props = schema.get("properties", {})
    # The JSON key must remain ``register`` (aliased from register_ internally).
    assert "register" in props
    assert "register_overlay" in props
    assert "brands" in props


async def test_resources_listed(client: Client):
    uris = {str(r.uri) for r in await client.list_resources()}
    assert {
        "klartext://brands",
        "klartext://platforms",
        "klartext://voice-dna",
        "klartext://brand-detection",
    } <= uris


async def test_resource_templates_listed(client: Client):
    templates = {str(t.uriTemplate) for t in await client.list_resource_templates()}
    assert "klartext://brands/{brand}" in templates
    assert "klartext://platforms/{platform}" in templates


async def test_brands_resource_matches_active_brands(client: Client):
    result = await client.read_resource("klartext://brands")
    data = json.loads(result[0].text)
    keys = {b["key"] for b in data["brands"]}
    assert keys == {"casey", "yorizon"}


async def test_brand_template_resource_casey_has_registers(client: Client):
    result = await client.read_resource("klartext://brands/casey")
    data = json.loads(result[0].text)
    assert data["name"] == "casey"
    assert set(data["registers"]) == {"personal", "professional"}


async def test_brand_template_resource_legacy_migration(client: Client):
    result = await client.read_resource("klartext://brands/cdit-works")
    data = json.loads(result[0].text)
    assert "error" in data
    assert "casey" in data["error"]
    assert data["active"] == ["casey", "yorizon"]


async def test_platform_template_resource(client: Client):
    result = await client.read_resource("klartext://platforms/blog")
    data = json.loads(result[0].text)
    assert data["platform"] == "blog"
    assert data["template"]


async def test_voice_dna_resource(client: Client):
    result = await client.read_resource("klartext://voice-dna")
    assert "## Voice DNA" in result[0].text


async def test_prompts_listed(client: Client):
    names = {p.name for p in await client.list_prompts()}
    assert {"draft_and_scan", "brand_voice_brief"} <= names


async def test_draft_and_scan_prompt_renders(client: Client):
    result = await client.get_prompt(
        "draft_and_scan", {"brief": "a post about NAS builds"}
    )
    assert result.messages
    text = result.messages[0].content.text
    assert "generate_text_context" in text
    assert "scan_draft" in text
    assert "a post about NAS builds" in text


async def test_brand_voice_brief_prompt_renders(client: Client):
    result = await client.get_prompt(
        "brand_voice_brief", {"brand": "casey", "register": "personal"}
    )
    text = result.messages[0].content.text
    assert "klartext://voice-dna" in text
    assert "klartext://brands/casey" in text
