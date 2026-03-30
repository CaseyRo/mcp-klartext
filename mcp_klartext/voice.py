"""Load and cache voice DNA, brand contexts, and bleed scan rules."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"


@dataclass
class BrandContext:
    name: str
    content: str


@dataclass
class VoiceData:
    voice_dna: str = ""
    brand_detection: str = ""
    brands: dict[str, BrandContext] = field(default_factory=dict)


def _extract_voice_dna(skill_content: str) -> str:
    """Extract the Voice DNA section from SKILL.md."""
    lines = skill_content.split("\n")
    capture = False
    result = []

    for line in lines:
        if line.startswith("## Voice DNA"):
            capture = True
            result.append(line)
            continue
        if capture:
            if line.startswith("## ") and "Voice DNA" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


def _extract_trilingual(skill_content: str) -> str:
    """Extract the Trilingual Workflow section from SKILL.md."""
    lines = skill_content.split("\n")
    capture = False
    result = []

    for line in lines:
        if line.startswith("## Trilingual Workflow"):
            capture = True
            result.append(line)
            continue
        if capture:
            if line.startswith("## ") and "Trilingual" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


def _extract_handshake(skill_content: str) -> str:
    """Extract the Image Prompt Handshake section from SKILL.md."""
    lines = skill_content.split("\n")
    capture = False
    result = []

    for line in lines:
        if line.startswith("## Image Prompt Handshake"):
            capture = True
            result.append(line)
            continue
        if capture:
            if line.startswith("## ") and "Handshake" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


def _extract_output_format(skill_content: str) -> str:
    """Extract the Output Format section from SKILL.md."""
    lines = skill_content.split("\n")
    capture = False
    result = []

    for line in lines:
        if line.startswith("## Output Format"):
            capture = True
            result.append(line)
            continue
        if capture:
            if line.startswith("## ") and "Output Format" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


def _extract_voice_calibration(skill_content: str) -> str:
    """Extract the Voice Calibration section from SKILL.md."""
    lines = skill_content.split("\n")
    capture = False
    result = []

    for line in lines:
        if line.startswith("## Voice Calibration"):
            capture = True
            result.append(line)
            continue
        if capture:
            if line.startswith("## ") and "Calibration" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


def _brand_key(filename: str) -> str:
    """Convert filename like 'casey-berlin.md' to context key 'casey.berlin'."""
    name = filename.replace(".md", "")
    mapping = {
        "casey-berlin": "casey.berlin",
        "cdit-works": "cdit-works",
        "storykeep": "storykeep",
        "nah": "nah",
        "yorizon": "yorizon",
    }
    return mapping.get(name, name)


def load_voice_data() -> VoiceData:
    """Load all voice data from bundled files."""
    data = VoiceData()

    # Load voice DNA from SKILL.md
    skill_path = DATA_DIR / "skill.md"
    if skill_path.exists():
        content = skill_path.read_text()
        data.voice_dna = _extract_voice_dna(content)
        trilingual = _extract_trilingual(content)
        handshake = _extract_handshake(content)
        output_format = _extract_output_format(content)
        calibration = _extract_voice_calibration(content)
        if trilingual:
            data.voice_dna += "\n\n" + trilingual
        if handshake:
            data.voice_dna += "\n\n" + handshake
        if output_format:
            data.voice_dna += "\n\n" + output_format
        if calibration:
            data.voice_dna += "\n\n" + calibration
    else:
        logger.warning("SKILL.md not found at %s", skill_path)

    # Load brand detection rules
    detection_path = DATA_DIR / "brand-detection.md"
    if detection_path.exists():
        data.brand_detection = detection_path.read_text().strip()
    else:
        logger.warning("brand-detection.md not found at %s", detection_path)

    # Load brand contexts
    brands_dir = DATA_DIR / "brands"
    if brands_dir.exists():
        for brand_file in sorted(brands_dir.glob("*.md")):
            key = _brand_key(brand_file.name)
            content = brand_file.read_text().strip()
            data.brands[key] = BrandContext(name=key, content=content)
            logger.info("Loaded brand context: %s", key)
    else:
        logger.warning("brands/ directory not found at %s", brands_dir)

    logger.info(
        "Voice data loaded: %d chars DNA, %d brands, %d chars detection",
        len(data.voice_dna),
        len(data.brands),
        len(data.brand_detection),
    )
    return data
