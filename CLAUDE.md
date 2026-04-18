# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependencies are managed with `uv`. Python >= 3.11.

```bash
uv sync                                   # install deps (incl. dev group)
uv sync --upgrade                         # bump locked versions within pyproject floors
uv run pytest                             # run full suite (pytest-asyncio auto mode)
uv run pytest tests/test_server.py -k generate_text   # single test by name
uv run ruff check .                       # lint
uv run ruff format .                      # format

TRANSPORT=http uv run python -m mcp_klartext.server   # run HTTP server on :8000
uv run mcp-klartext                                   # run stdio server (default)

docker compose up                         # run HTTP server on :8008 (maps to container :8000)
docker compose build                      # rebuild after code/dep changes
```

Release is automated: any push to `main` that changes non-doc files triggers `.github/workflows/release.yml`, which bumps the patch in `pyproject.toml`, appends to `CHANGELOG.md`, tags `vX.Y.Z`, and builds/pushes a multi-arch image to `ghcr.io/caseyro/mcp-klartext`. Include `[skip ci]` in the commit message to skip. Do not hand-edit `version` in `pyproject.toml` — the CI owns it.

## Architecture

This is a FastMCP 3.x server that serves brand-aware copywriting context (voice DNA, brand rules, platform templates) as MCP tools. It is content-only — it does not generate text, it returns markdown rules for the calling LLM to follow.

**Startup flow** (`mcp_klartext/server.py`):
1. `load_voice_data()` reads `data/skill.md` and slices it by H2 headers (`## Voice DNA`, `## Trilingual Workflow`, `## Image Prompt Handshake`, `## Output Format`, `## Voice Calibration`, `## AI Bleed Scan`) into a single concatenated `voice_dna` string. Changing section titles in `skill.md` breaks the section extractor — the slicing is string-literal based in `voice.py`. To add a new section, add a matching `_extract_*` helper and wire it in `load_voice_data()`.
2. `data/brands/*.md` are loaded into `BrandContext` entries. Filenames are mapped to `@`-prefixed keys via `_brand_key()` in `voice.py` (e.g. `casey-berlin.md` → `casey.berlin`). New brands require updating that mapping.
3. `data/platforms/*.md` are loaded by `load_platforms()`; the filename (minus `.md`) is the key.
4. A `BearerTokenVerifier` (`auth.py`) is attached to the FastMCP instance only if `MCP_API_KEY` is set in the environment. Bearer is the only auth path — if you see references to Keycloak/OIDC anywhere, it's stale, delete it. Auth is optional for local stdio use, required in production HTTP deployments.

**Tools exposed**:
- `generate_text_context` — one-shot that merges voice + brand + platform. The docstring explicitly nudges callers here to avoid round-trips.
- `get_voice_dna`, `get_brand_context`, `get_platform_template`, `list_platforms` — granular accessors (read-only content).
- `scan_draft(text)` — runs the AI Bleed Scan rubric (see `data/skill.md`) programmatically via `mcp_klartext/scanner.py`. Returns `{issues, stats, clean}` with per-pattern severity and line numbers. Expected usage: caller generates with `generate_text_context`, then runs `scan_draft` as a second pass before finalizing. Pattern lists live in `LEXICAL_TELLS` and `PHRASE_TELLS` at the top of `scanner.py` — update those together with the rubric text in `skill.md` so instructions and enforcement stay in sync.
- `portal_routing_guide` — hard-coded map of sibling MCP servers in the CDIT portal; not data-driven, edit in `server.py` when the portal topology changes.

Tool descriptions are prefixed with domain tags (`[content]`, `[infra]`) to help the portal disambiguate across servers — preserve these when editing.

**Platform literal** — `get_platform_template`'s `platform` argument is a `Literal[...]` union in `server.py`. Adding a new `data/platforms/*.md` file also requires extending that Literal, or the new platform is loadable but not selectable via the typed tool.

**Transport** (`config.py`): `TRANSPORT=stdio` (default) or `TRANSPORT=http`. HTTP uses FastMCP's `streamable-http`. `HOST`/`PORT` override host/port. Settings come from env via `pydantic-settings`.

**Deployment**: Komodo stack `git-mcp-klartext` (see `komodo.toml`) deploys from the `main` branch on `ubuntu-smurf-mirror`, exposed at `https://mcp-klartext.cdit-dev.de/mcp` through the Cloudflare MCP Portal. The stack injects `MCP_API_KEY` (sourced from the Komodo variable `MCP_KLARTEXT_API_KEY`) — the env name must match what `server.py` reads or auth silently no-ops. Clients authenticate with portal-brokered tokens via OAuth, not the raw `MCP_API_KEY` (that's the upstream credential the portal uses).

**Client registration**: In Claude Code, klartext is registered in `~/.claude/mcp.json` as a `streamable-http` server with no static bearer — Claude Code picks up the 401 from the portal and runs the OAuth flow. There is no longer a local `~/.claude/skills/klartext/` skill: the MCP is the single source of truth. When you change voice DNA, platform templates, or brand contexts, edit `data/**/*.md` here and let CI deploy — every client (Claude.ai, Claude Code, n8n) gets the change from the same server.

## Conventions

- Tests live in `tests/` and cover the loaders (`test_voice.py`, `test_platforms.py`), bearer auth (`test_auth.py`), and every tool via FastMCP's in-memory `Client(mcp)` (`test_server.py`). Prefer the in-memory client over HTTP for tool tests — no transport, no port, still exercises the real dispatch.
- Markdown data files are authoritative content. Edits to `data/**/*.md` ship to callers verbatim — treat them as user-facing copy, not code comments.
- OpenSpec (`openspec/`) is present but the `specs/` directory is empty; use `/opsx:new` or the openspec skills for spec-driven changes.
