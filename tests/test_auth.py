"""Tests for bearer token authentication."""

from __future__ import annotations

import pytest

from mcp_klartext.auth import BearerTokenVerifier


@pytest.fixture
def verifier() -> BearerTokenVerifier:
    return BearerTokenVerifier(api_key="secret-token")


async def test_verify_token_accepts_exact_match(verifier: BearerTokenVerifier):
    result = await verifier.verify_token("secret-token")
    assert result is not None
    assert result.token == "secret-token"
    assert result.client_id == "bearer"
    assert result.scopes == []


async def test_verify_token_rejects_wrong_token(verifier: BearerTokenVerifier):
    assert await verifier.verify_token("wrong") is None


async def test_verify_token_rejects_empty_token(verifier: BearerTokenVerifier):
    assert await verifier.verify_token("") is None


async def test_verify_token_rejects_prefix_match(verifier: BearerTokenVerifier):
    assert await verifier.verify_token("secret") is None


async def test_empty_api_key_rejects_empty_input():
    empty = BearerTokenVerifier(api_key="")
    assert await empty.verify_token("anything") is None
