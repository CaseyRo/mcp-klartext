"""Load and cache platform templates."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data" / "platforms"


@dataclass
class PlatformTemplate:
    name: str
    content: str
    summary: str


def _extract_summary(content: str) -> str:
    """Extract a brief summary from the platform template frontmatter or first paragraph."""
    lines = content.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            return stripped[:200]
    return ""


def _platform_key(filename: str) -> str:
    """Convert filename like 'linkedin-post.md' to platform key."""
    return filename.replace(".md", "")


def load_platforms() -> dict[str, PlatformTemplate]:
    """Load all platform templates from bundled files."""
    platforms: dict[str, PlatformTemplate] = {}

    if not DATA_DIR.exists():
        logger.warning("platforms/ directory not found at %s", DATA_DIR)
        return platforms

    for template_file in sorted(DATA_DIR.glob("*.md")):
        key = _platform_key(template_file.name)
        content = template_file.read_text().strip()
        summary = _extract_summary(content)
        platforms[key] = PlatformTemplate(name=key, content=content, summary=summary)
        logger.info("Loaded platform template: %s", key)

    logger.info("Platforms loaded: %d templates", len(platforms))
    return platforms
