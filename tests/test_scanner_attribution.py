"""Tests for attribution checks in scanner.scan_for_ai_tells.

NO_READMORE — warning when frontmatter has references but body lacks a
              Read more / Weiterlesen heading.
UNCAPTIONED_AI_IMAGE — error when a Bildsprache image embed lacks an AI
                        attribution marker in alt/adjacent caption.
"""

from __future__ import annotations

from mcp_klartext.scanner import scan_for_ai_tells


def _attribution_codes(result: dict) -> list[str]:
    return [i["pattern"] for i in result["issues"] if i["category"] == "attribution"]


class TestAttributionScan:
    def test_no_frontmatter_no_attribution_block(self) -> None:
        result = scan_for_ai_tells("Just a plain body with no frontmatter.\n")
        assert result["attribution"]["references_count"] == 0
        assert result["attribution"]["ai_images_total"] == 0
        assert result["attribution"]["readmore_rendered"] is False
        assert "NO_READMORE" not in _attribution_codes(result)

    def test_references_without_readmore_warns(self) -> None:
        text = (
            "---\n"
            "title: Post\n"
            "references:\n"
            "  - type: url\n"
            "    href: https://example.com\n"
            "---\n"
            "A plain body with no Read more section.\n"
        )
        result = scan_for_ai_tells(text)
        codes = _attribution_codes(result)
        assert "NO_READMORE" in codes
        issue = next(i for i in result["issues"] if i["pattern"] == "NO_READMORE")
        assert issue["severity"] == "medium"  # warning-tier

    def test_references_with_readmore_passes(self) -> None:
        text = (
            "---\n"
            "references:\n"
            "  - type: url\n"
            "    href: https://example.com\n"
            "---\n"
            "Body.\n\n## Read more\n\n- [Source](https://example.com)\n"
        )
        result = scan_for_ai_tells(text)
        assert "NO_READMORE" not in _attribution_codes(result)
        assert result["attribution"]["readmore_rendered"] is True
        assert result["attribution"]["references_count"] == 1

    def test_empty_references_does_not_warn(self) -> None:
        text = "---\nreferences: []\n---\nBody.\n"
        result = scan_for_ai_tells(text)
        assert "NO_READMORE" not in _attribution_codes(result)

    def test_uncaptioned_ai_image_errors(self) -> None:
        text = (
            "Some copy.\n\n"
            "![](https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n\n"
            "More copy with no AI marker.\n"
        )
        result = scan_for_ai_tells(text)
        codes = _attribution_codes(result)
        assert "UNCAPTIONED_AI_IMAGE" in codes
        issue = next(
            i for i in result["issues"] if i["pattern"] == "UNCAPTIONED_AI_IMAGE"
        )
        assert issue["severity"] == "high"
        assert result["attribution"]["ai_images_total"] == 1
        assert result["attribution"]["ai_images_captioned"] == 0

    def test_captioned_ai_image_passes(self) -> None:
        text = (
            "![AI-generated morning walk in Kreuzberg]"
            "(https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n"
        )
        result = scan_for_ai_tells(text)
        assert "UNCAPTIONED_AI_IMAGE" not in _attribution_codes(result)
        assert result["attribution"]["ai_images_captioned"] == 1

    def test_non_bildsprache_image_not_flagged(self) -> None:
        text = "![vacation photo](https://cdn.other.example/pic.jpg)\n"
        result = scan_for_ai_tells(text)
        assert "UNCAPTIONED_AI_IMAGE" not in _attribution_codes(result)
        assert result["attribution"]["ai_images_total"] == 0

    def test_diagnostics_block_present(self) -> None:
        text = (
            "---\n"
            "references:\n"
            "  - type: stolperstein\n"
            "    id: SK-0481\n"
            "---\n"
            "Body.\n"
            "![AI-generated](https://img.cdit-works.de/x/y-1024x1024.webp)\n"
        )
        result = scan_for_ai_tells(text)
        diag = result["attribution"]
        assert set(diag.keys()) == {
            "ai_images_total",
            "ai_images_captioned",
            "references_count",
            "readmore_rendered",
        }

    def test_scan_still_runs_voice_checks_on_body(self) -> None:
        text = (
            "---\n"
            "title: Test\n"
            "---\n"
            "Let's dive in and leverage this seamlessly robust approach.\n"
        )
        result = scan_for_ai_tells(text)
        # Voice bleed checks still fire against the body.
        assert result["stats"]["high"] > 0
        assert any(i["pattern"] == "leverage" for i in result["issues"])

    def test_frontmatter_contents_do_not_trigger_bleed_checks(self) -> None:
        # A frontmatter that happens to contain tell-words shouldn't be
        # scanned as copy.
        text = (
            "---\n"
            "notes: we leverage this robust seamless thing\n"
            "---\n"
            "Clean body.\n"
        )
        result = scan_for_ai_tells(text)
        # Frontmatter words were stripped before bleed scan
        assert not any(i["pattern"] == "leverage" for i in result["issues"])
