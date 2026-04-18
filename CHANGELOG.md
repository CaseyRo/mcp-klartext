# Changelog

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
