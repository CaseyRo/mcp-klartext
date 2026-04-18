"""Tests for platform template loading."""

from __future__ import annotations

from mcp_klartext.platforms import _extract_summary, _platform_key, load_platforms


def test_platform_key_strips_md_extension():
    assert _platform_key("linkedin-post.md") == "linkedin-post"
    assert _platform_key("blog.md") == "blog"


def test_extract_summary_skips_headers_and_separators():
    content = "# Title\n\n---\n\nFirst real paragraph here.\n\nSecond."
    assert _extract_summary(content) == "First real paragraph here."


def test_extract_summary_truncates_at_200_chars():
    long = "a" * 500
    assert len(_extract_summary(long)) == 200


def test_extract_summary_returns_empty_for_only_headers():
    assert _extract_summary("# only a header") == ""


def test_load_platforms_bundled():
    platforms = load_platforms()
    expected = {
        "blog",
        "instagram",
        "linkedin-article",
        "linkedin-post",
        "newsletter",
        "proposal",
        "reflection",
        "whatsapp",
    }
    assert set(platforms) == expected

    for key, tmpl in platforms.items():
        assert tmpl.name == key
        assert tmpl.content, f"platform {key} has empty content"
