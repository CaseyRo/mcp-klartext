"""Tests for brand-slug normalisation (May 2026 brand collapse)."""

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
            # @-prefixed variants resolve to active brand keys.
            ("@casey", "casey"),
            ("@yorizon", "yorizon"),
            # Already canonical.
            ("casey", "casey"),
            ("yorizon", "yorizon"),
        ],
    )
    def test_known_aliases(self, alias: str, canonical: str) -> None:
        assert normalize_brand(alias) == canonical

    def test_none_passes_through(self) -> None:
        assert normalize_brand(None) is None

    def test_unknown_passes_through(self) -> None:
        # Removed brands (casey-berlin, cdit-works, storykeep, nah) and
        # any other unknown string pass through unchanged. The server
        # layer's _REMOVED_BRANDS map handles the migration message.
        assert normalize_brand("casey-berlin") == "casey-berlin"
        assert normalize_brand("totally-unknown") == "totally-unknown"

    def test_canonical_brands_are_active_only(self) -> None:
        # May 2026 brand collapse: only casey + yorizon remain.
        assert set(CANONICAL_BRANDS) == {"casey", "yorizon"}


class TestLookupBrand:
    @pytest.fixture
    def brands_dict(self):
        from mcp_klartext.voice import BrandContext

        return {
            "casey": BrandContext(name="casey", content="casey rules"),
            "yorizon": BrandContext(name="yorizon", content="yorizon rules"),
        }

    def test_canonical_lookup_casey(self, brands_dict):
        b = lookup_brand(brands_dict, "casey")
        assert b.content == "casey rules"

    def test_canonical_lookup_yorizon(self, brands_dict):
        b = lookup_brand(brands_dict, "yorizon")
        assert b.content == "yorizon rules"

    def test_at_prefixed_casey_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "@casey")
        assert b.content == "casey rules"

    def test_at_prefixed_yorizon_resolves(self, brands_dict):
        b = lookup_brand(brands_dict, "@yorizon")
        assert b.content == "yorizon rules"

    def test_removed_brand_returns_none(self, brands_dict):
        # Removed brands no longer resolve — the server layer's
        # _REMOVED_BRANDS map intercepts before this lookup.
        assert lookup_brand(brands_dict, "casey-berlin") is None
        assert lookup_brand(brands_dict, "cdit-works") is None
        assert lookup_brand(brands_dict, "storykeep") is None
        assert lookup_brand(brands_dict, "nah") is None

    def test_unknown_returns_none(self, brands_dict):
        assert lookup_brand(brands_dict, "nope") is None

    def test_none_context_returns_none(self, brands_dict):
        assert lookup_brand(brands_dict, None) is None
