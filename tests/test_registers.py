"""Tests for the casey brand's register overlay system (May 2026 collapse)."""

from __future__ import annotations

import pytest
from fastmcp.client.client import Client

from mcp_klartext.server import mcp
from mcp_klartext.voice import _extract_registers, load_voice_data


def _payload(result):
    """FastMCP returns a CallToolResult; pull the JSON content out."""
    if hasattr(result, "data") and result.data is not None:
        return result.data
    if hasattr(result, "content") and result.content:
        first = result.content[0]
        if hasattr(first, "text"):
            import json

            return json.loads(first.text)
    raise AssertionError(f"Unexpected result shape: {result!r}")


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


# -- Loader-level tests -----------------------------------------------------


def test_extract_registers_finds_personal_and_professional():
    content = """
# casey

Some shared voice content.

## Registers

### personal — recognition surface

Personal-only direction.

### professional — verification surface

Professional-only direction.

## Visual

(more brand content)
""".strip()

    registers = _extract_registers(content)

    assert set(registers.keys()) == {"personal", "professional"}
    assert "Personal-only direction" in registers["personal"].content
    assert "Professional-only direction" in registers["professional"].content


def test_extract_registers_filters_unknown_names():
    content = """
## Registers

### personal

ok

### marketing

should be ignored — not a valid register
""".strip()

    registers = _extract_registers(content)

    assert "personal" in registers
    assert "marketing" not in registers


def test_extract_registers_returns_empty_when_no_section():
    content = "# yorizon\n\nNo registers here."
    assert _extract_registers(content) == {}


def test_loaded_casey_has_both_registers():
    data = load_voice_data()
    casey = data.brands["casey"]

    assert set(casey.registers.keys()) == {"personal", "professional"}
    assert casey.registers["personal"].content
    assert casey.registers["professional"].content


def test_loaded_yorizon_has_no_registers():
    data = load_voice_data()
    yorizon = data.brands["yorizon"]
    assert yorizon.registers == {}


# -- Tool-level tests -------------------------------------------------------


async def test_get_brand_context_casey_personal_overlay(client: Client):
    result = await client.call_tool(
        "get_brand_context", {"context": "casey", "register": "personal"}
    )
    payload = _payload(result)

    assert payload["context"] == "casey"
    assert payload["register"] == "personal"
    assert payload["register_overlay"]
    assert "recognition" in payload["register_overlay"].lower()


async def test_get_brand_context_casey_professional_overlay(client: Client):
    result = await client.call_tool(
        "get_brand_context", {"context": "casey", "register": "professional"}
    )
    payload = _payload(result)

    assert payload["register"] == "professional"
    assert "verification" in payload["register_overlay"].lower()


async def test_get_brand_context_casey_invalid_register_raises(client: Client):
    # Pydantic enforces the Literal type at the tool boundary, so
    # "marketing" never reaches our handler. The MCP client surfaces
    # this as a ToolError / ValidationError. We just confirm the call
    # does not silently succeed.
    import pytest

    with pytest.raises(Exception) as exc_info:
        await client.call_tool(
            "get_brand_context", {"context": "casey", "register": "marketing"}
        )
    msg = str(exc_info.value).lower()
    assert "personal" in msg or "professional" in msg or "literal" in msg


async def test_yorizon_register_rejected(client: Client):
    result = await client.call_tool(
        "get_brand_context",
        {"context": "yorizon", "register": "professional"},
    )
    payload = _payload(result)

    assert "error" in payload
    assert "yorizon" in payload["error"].lower()
    assert "register" in payload["error"].lower()


async def test_generate_text_context_register_required_for_casey(client: Client):
    result = await client.call_tool(
        "generate_text_context",
        {"context": "casey", "platform": "blog", "language": "en"},
    )
    payload = _payload(result)

    bc = payload["brand_context"]
    assert bc["name"] == "casey"
    # No register passed → response signals which registers are valid.
    assert bc.get("register_required") is True
    assert set(bc["register_options"]) == {"personal", "professional"}


async def test_generate_text_context_with_personal_register(client: Client):
    result = await client.call_tool(
        "generate_text_context",
        {
            "context": "casey",
            "platform": "blog",
            "language": "en",
            "register": "personal",
        },
    )
    payload = _payload(result)

    bc = payload["brand_context"]
    assert bc["name"] == "casey"
    assert bc["register"] == "personal"
    assert bc["register_overlay"]
