"""Tests for brand-slug normalisation (CDI-1041 cross-skill alignment)."""

from __future__ import annotations

import pytest

from mcp_klartext.brands import (
    CANONICAL_BRANDS,
    lookup_brand,
    normalize_brand,
)


class TestNormalizeBrand:
    @pytest.mark.parametrize(
        "alias,canonical",
        [
            ("@casey.berlin", "casey-berlin"),
            ("casey.berlin", "casey-berlin"),
            ("@cdit", "cdit-works"),
            ("cdit", "cdit-works"),
            ("@cdit-works", "cdit-works"),
            ("@cdit.works", "cdit-works"),
            ("cdit-works.de", "cdit-works"),
            ("cdit.works", "cdit-works"),
            ("@storykeep", "storykeep"),
            ("@nah", "nah"),
            ("@yorizon", "yorizon"),
            ("casey_berlin", "casey-berlin"),
            ("cdit_works", "cdit-works"),
            # Already canonical
            ("casey-berlin", "casey-berlin"),
            ("cdit-works", "cdit-works"),
        ],
    )
    def test_known_aliases(self, alias: str, canonical: str) -> None:
        assert normalize_brand(alias) == canonical

    def test_none_passes_through(self) -> None:
        assert normalize_brand(None) is None

    def test_unknown_passes_through(self) -> None:
        assert normalize_brand("totally-unknown") == "totally-unknown"

    def test_canonical_brands_are_complete(self) -> None:
        # The brand-detection map and the brand md files should align.
        expected = {"casey-berlin", "cdit-works", "storykeep", "nah", "yorizon"}
        assert set(CANONICAL_BRANDS) == expected


class TestLookupBrand:
    @pytest.fixture
    def brands_dict(self):
        from mcp_klartext.voice import BrandContext

        return {
            "casey-berlin": BrandContext(name="casey-berlin", content="casey rules"),
            "cdit-works": BrandContext(name="cdit-works", content="cdit rules"),
        }

    def test_canonical_lookup(self, brands_dict):
        b = lookup_brand(brands_dict, "casey-berlin")
        assert b.content == "casey rules"

    def test_legacy_dot_form_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "casey.berlin")
        assert b.content == "casey rules"

    def test_legacy_at_prefixed_form_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "@casey.berlin")
        assert b.content == "casey rules"

    def test_legacy_cdit_abbreviation_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "@cdit")
        assert b.content == "cdit rules"

    def test_legacy_cdit_works_de_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "cdit-works.de")
        assert b.content == "cdit rules"

    def test_unknown_returns_none(self, brands_dict):
        assert lookup_brand(brands_dict, "nope") is None

    def test_none_context_returns_none(self, brands_dict):
        assert lookup_brand(brands_dict, None) is None
