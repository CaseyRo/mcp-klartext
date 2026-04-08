"""Configuration loaded from environment variables."""

from __future__ import annotations

import logging
from typing import Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Server transport
    transport: Literal["stdio", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
