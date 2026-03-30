# mcp-klartext

MCP server for brand-aware copywriting — provides Casey Romkes' voice DNA, brand contexts, and platform templates as structured MCP tools.

## Tools

- `generate_text_context` — Complete writing context (voice DNA + brand + platform + bleed rules)
- `get_voice_dna` — Voice DNA rules only
- `get_brand_context` — Brand-specific voice/visual/language settings
- `list_platforms` — Available platform templates
- `get_platform_template` — Specific platform template

## Usage

```bash
# Local development
TRANSPORT=http python -m mcp_klartext.server

# Docker
docker compose up
```

## Authentication

- **Claude.ai**: Keycloak OAuth (confidential OIDC client `mcp-klartext`)
- **Claude Code / n8n**: Bearer token (`Authorization: Bearer bmcp_...`)
