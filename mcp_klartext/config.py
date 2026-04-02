"""Configuration loaded from environment variables."""

from __future__ import annotations

import logging
import secrets
from typing import Any, Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Server transport
    transport: Literal["stdio", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

    # MCP server auth
    mcp_klartext_api_key: str = ""
    mcp_klartext_public_url: str = ""

    # Keycloak OIDC
    keycloak_issuer: str = "https://auth.cdit-works.de/realms/cdit-mcp"
    keycloak_audience: str = "mcp-klartext"
    keycloak_client_id: str = "mcp-klartext"
    keycloak_client_secret: str = ""

    model_config = {"env_prefix": "", "case_sensitive": False}

    def ensure_api_key(self) -> str:
        """Return the API key, generating one if not configured."""
        if self.mcp_klartext_api_key:
            return self.mcp_klartext_api_key

        from mcp_klartext.auth import generate_api_key

        key = generate_api_key()
        self.mcp_klartext_api_key = key
        logger.warning("Generated API key: %s (set MCP_KLARTEXT_API_KEY to persist)", key)
        return key

    @property
    def base_url(self) -> str:
        """Public URL for OAuth metadata, or computed from host:port."""
        if self.mcp_klartext_public_url:
            return self.mcp_klartext_public_url.rstrip("/")
        return f"http://{self.host}:{self.port}"


settings = Settings()
