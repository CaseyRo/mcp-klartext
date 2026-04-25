# Changelog

## [0.2.9] - 2026-04-25

- feat(references): reference surfacing + AI image attribution scan (CDI-1014) (#10)


## [0.2.8] - 2026-04-21

- fix(security): SecretStr for MCP_API_KEY, add __main__.py + py.typed


## [0.2.6] - 2026-04-18

- chore: add Dependabot config for pip, actions, docker


## [0.2.5] - 2026-04-18

- feat(reliability): stateless_http, /health, fail-fast auth


## [0.2.4] - 2026-04-18

- chore: switch compose to ghcr image; bump Actions to Node 24 majors


## [0.2.2] - 2026-04-09

- fix: lowercase Docker image tags in release CI


## [0.2.0] - 2026-04-09

### Changed
- Bumped FastMCP dependency to >=3.2.2
- Improved generate_text_context docstring to guide LLMs toward using this single call
- get_platform_template platform parameter now uses Literal enum for type safety

### Added
- Automated version bump and release CI via GitHub Actions
- CHANGELOG.md for tracking changes
