# mcp-klartext

MCP server for brand-aware copywriting — provides Casey Romkes' voice DNA, brand contexts, and platform templates as structured MCP tools.

## Tools

- `generate_text_context` — Complete writing context (voice DNA + brand + register overlay + platform + bleed rules)
- `get_voice_dna` — Voice DNA rules only
- `get_brand_context` — Brand-specific voice/visual/language settings, with optional `register` overlay (casey only)
- `list_platforms` — Available platform templates
- `get_platform_template` — Specific platform template
- `scan_draft` — AI-tell bleed scan, with optional `brand="casey"` to enforce May 2026 hard rules

## Brands and registers

Active brands (May 2026 collapse): **casey**, **yorizon**.

The `casey` brand carries one shared voice DNA across two registers:

- `personal` — recognition surface, manifesto-adjacent, kitchen-table tone (casey.berlin)
- `professional` — verification surface, workshop voice, "what I shipped" frame (cdit-works.de)

The previous `casey-berlin`, `cdit-works`, `storykeep`, and `nah` brand keys return a migration error pointing at the correct `casey` + register combination. Yorizon is fully isolated (no registers, "we" voice).

## Usage

```bash
# Local development
TRANSPORT=http python -m mcp_klartext.server

# Docker
docker compose up
```

## Authentication

Bearer token via `MCP_API_KEY`. Clients send `Authorization: Bearer <token>`. If `MCP_API_KEY` is unset the server runs unauthenticated — only do this for local stdio use.
