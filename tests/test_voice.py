"""Tests for voice DNA loading and section extraction."""

from __future__ import annotations

from mcp_klartext.voice import (
    _brand_key,
    _extract_ai_bleed_scan,
    _extract_handshake,
    _extract_output_format,
    _extract_trilingual,
    _extract_voice_calibration,
    _extract_voice_dna,
    load_voice_data,
)


SAMPLE = """# Skill

## Voice DNA
voice rules here

more voice

## Trilingual Workflow
trilingual rules

## Image Prompt Handshake
handshake rules

## Output Format
output rules

## Voice Calibration
calibration rules

## AI Bleed Scan
bleed scan rules

## Unrelated
should not appear
"""


def test_extract_voice_dna_captures_section():
    result = _extract_voice_dna(SAMPLE)
    assert result.startswith("## Voice DNA")
    assert "voice rules here" in result
    assert "trilingual rules" not in result


def test_extract_trilingual_captures_section():
    result = _extract_trilingual(SAMPLE)
    assert result.startswith("## Trilingual Workflow")
    assert "trilingual rules" in result
    assert "handshake rules" not in result


def test_extract_handshake_captures_section():
    assert "handshake rules" in _extract_handshake(SAMPLE)


def test_extract_output_format_captures_section():
    assert "output rules" in _extract_output_format(SAMPLE)


def test_extract_voice_calibration_captures_section():
    assert "calibration rules" in _extract_voice_calibration(SAMPLE)


def test_extract_ai_bleed_scan_captures_section():
    result = _extract_ai_bleed_scan(SAMPLE)
    assert result.startswith("## AI Bleed Scan")
    assert "bleed scan rules" in result
    assert "should not appear" not in result


def test_extract_returns_empty_when_section_missing():
    assert _extract_voice_dna("# no sections here") == ""
    assert _extract_ai_bleed_scan("# no sections here") == ""


def test_brand_key_known_mappings():
    # CDI-1041: canonical bare-slug form across the fleet.
    assert _brand_key("casey-berlin.md") == "casey-berlin"
    assert _brand_key("cdit-works.md") == "cdit-works"
    assert _brand_key("storykeep.md") == "storykeep"
    assert _brand_key("nah.md") == "nah"
    assert _brand_key("yorizon.md") == "yorizon"


def test_brand_key_unknown_falls_back_to_stem():
    assert _brand_key("new-brand.md") == "new-brand"


def test_load_voice_data_from_bundled_files():
    data = load_voice_data()

    assert data.voice_dna, "voice DNA should not be empty"
    assert "## Voice DNA" in data.voice_dna
    assert "## AI Bleed Scan" in data.voice_dna, (
        "AI Bleed Scan must be shipped with voice DNA"
    )

    assert data.brand_detection, "brand detection rules should not be empty"
    assert "Override Tags" in data.brand_detection

    # CDI-1041 — canonical bare-slug form across the fleet.
    expected_brands = {"casey-berlin", "cdit-works", "storykeep", "nah", "yorizon"}
    assert set(data.brands) == expected_brands

    for key, brand in data.brands.items():
        assert brand.name == key
        assert brand.content, f"brand {key} has empty content"
