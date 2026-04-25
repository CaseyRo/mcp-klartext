"""Tests for reference surfacing — frontmatter parsing, Read more, captions, image detection."""

from __future__ import annotations

from mcp_klartext.references import (
    Reference,
    detect_image_embeds,
    has_readmore_heading,
    parse_frontmatter,
    references_from_frontmatter,
    render_ai_caption,
    render_readmore,
)


class TestParseFrontmatter:
    def test_no_frontmatter(self) -> None:
        meta, body = parse_frontmatter("Just a markdown body.\n")
        assert meta == {}
        assert body == "Just a markdown body.\n"

    def test_simple_frontmatter(self) -> None:
        text = "---\ntitle: Hello\nlanguage: de\n---\nBody here.\n"
        meta, body = parse_frontmatter(text)
        assert meta["title"] == "Hello"
        assert meta["language"] == "de"
        assert body == "Body here.\n"

    def test_frontmatter_with_references(self) -> None:
        text = (
            "---\n"
            "title: Test\n"
            "references:\n"
            "  - type: stolperstein\n"
            "    id: SK-0481\n"
            "    title: A Kreuzberg entry\n"
            "  - type: url\n"
            "    href: https://example.com\n"
            "    title: Source article\n"
            "---\n"
            "Body.\n"
        )
        meta, body = parse_frontmatter(text)
        refs = references_from_frontmatter(meta)
        assert len(refs) == 2
        assert refs[0].type == "stolperstein"
        assert refs[0].id == "SK-0481"
        assert refs[1].type == "url"
        assert refs[1].href == "https://example.com"

    def test_frontmatter_rejects_malformed_refs(self) -> None:
        text = (
            "---\n"
            "references:\n"
            "  - not-a-dict\n"
            "  - type: nonsense\n"
            "    id: X\n"
            "  - type: url\n"
            "    href: https://ok.example\n"
            "---\n"
        )
        meta, _ = parse_frontmatter(text)
        refs = references_from_frontmatter(meta)
        # Only the well-formed url entry survives filtering.
        assert len(refs) == 1
        assert refs[0].type == "url"


class TestRenderReadmore:
    def test_empty_returns_empty(self) -> None:
        assert render_readmore([]) == ""

    def test_english_heading(self) -> None:
        out = render_readmore(
            [Reference(type="url", href="https://example.com", title="Example")],
            language="en",
        )
        assert out.startswith("## Read more")
        assert "https://example.com" in out
        assert "Example" in out

    def test_german_heading(self) -> None:
        out = render_readmore(
            [Reference(type="url", href="https://example.de", title="Beispiel")],
            language="de",
        )
        assert out.startswith("## Weiterlesen")

    def test_stolperstein_renders_internal_link(self) -> None:
        out = render_readmore(
            [Reference(type="stolperstein", id="SK-0481", title="A note")]
        )
        assert "stolperstein://SK-0481" in out
        assert "A note" in out

    def test_document_renders_plain_citation(self) -> None:
        out = render_readmore(
            [Reference(type="document", title="Interview transcript")]
        )
        # No link markdown
        assert "]" not in out.splitlines()[-2]
        assert "Interview transcript" in out

    def test_fallback_title_from_url_host(self) -> None:
        out = render_readmore(
            [Reference(type="url", href="https://example.com/deep/path")]
        )
        assert "example.com" in out


class TestRenderAiCaption:
    def test_english_caption(self) -> None:
        attr = {
            "provider": "openai",
            "model": "gpt-image-2",
            "prompt_anchor": "A quiet Berlin courtyard in winter",
        }
        cap = render_ai_caption(attr, language="en")
        assert "A quiet Berlin courtyard in winter" in cap
        assert "AI-generated with openai/gpt-image-2" in cap

    def test_german_caption(self) -> None:
        attr = {
            "provider": "openai",
            "model": "gpt-image-2",
            "prompt_anchor": "Ein ruhiger Berliner Hinterhof",
        }
        cap = render_ai_caption(attr, language="de")
        assert "KI-generiert mit openai/gpt-image-2" in cap

    def test_missing_anchor_still_produces_attribution(self) -> None:
        cap = render_ai_caption({"provider": "bfl", "model": "flux-2-flex"})
        assert "AI-generated with bfl/flux-2-flex" in cap

    def test_long_anchor_truncated(self) -> None:
        long_text = "word " * 200
        attr = {"provider": "x", "model": "y", "prompt_anchor": long_text}
        cap = render_ai_caption(attr)
        assert len(cap.split(" — ")[0]) <= 140


class TestDetectImageEmbeds:
    def test_bildsprache_detected(self) -> None:
        body = "Some text ![A morning walk](https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n"
        embeds = detect_image_embeds(body)
        assert len(embeds) == 1
        assert embeds[0].is_bildsprache is True
        assert embeds[0].src == "https://img.cdit-works.de/casey-berlin/walk-1200x630.webp"

    def test_non_bildsprache_not_flagged(self) -> None:
        body = "![external](https://cdn.example.com/photo.jpg)\n"
        embeds = detect_image_embeds(body)
        assert len(embeds) == 1
        assert embeds[0].is_bildsprache is False

    def test_ai_caption_in_alt_detected(self) -> None:
        body = "![AI-generated morning walk](https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n"
        embeds = detect_image_embeds(body)
        assert embeds[0].has_ai_caption is True

    def test_ai_caption_on_following_line_detected(self) -> None:
        body = (
            "![](https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n"
            "*AI-generated with openai/gpt-image-2*\n"
        )
        embeds = detect_image_embeds(body)
        assert embeds[0].has_ai_caption is True

    def test_empty_alt_no_caption_flagged(self) -> None:
        body = "![](https://img.cdit-works.de/casey-berlin/walk-1200x630.webp)\n\nNext paragraph with no AI marker.\n"
        embeds = detect_image_embeds(body)
        assert embeds[0].is_bildsprache is True
        assert embeds[0].has_ai_caption is False

    def test_german_ki_marker_detected(self) -> None:
        body = "![KI-generiert mit openai](https://img.cdit-works.de/x/y-1024x1024.webp)\n"
        embeds = detect_image_embeds(body)
        assert embeds[0].has_ai_caption is True


class TestHasReadmoreHeading:
    def test_english(self) -> None:
        assert has_readmore_heading("## Read more\n\n- link\n") is True

    def test_german(self) -> None:
        assert has_readmore_heading("## Weiterlesen\n") is True

    def test_dutch(self) -> None:
        assert has_readmore_heading("## Lees verder\n") is True

    def test_h3_also_accepted(self) -> None:
        assert has_readmore_heading("### Read more\n") is True

    def test_none_returns_false(self) -> None:
        assert has_readmore_heading("Just a body\n\n## Other heading\n") is False
