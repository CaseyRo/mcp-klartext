"""Configuration loaded from environment variables."""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Server transport
    transport: Literal["stdio", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

    # Bearer token auth for MCP Portal
    mcp_api_key: SecretStr = SecretStr("")

    model_config = {"env_prefix": "", "case_sensitive": False}

    @model_validator(mode="after")
    def require_api_key_for_http(self) -> "Settings":
        if self.transport == "http" and not self.mcp_api_key.get_secret_value():
            raise ValueError(
                "MCP_API_KEY is required when TRANSPORT=http. "
                "Refusing to start an unauthenticated server."
            )
        return self


settings = Settings()
