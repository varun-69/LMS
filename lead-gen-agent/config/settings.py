"""
Central settings loaded from environment variables / .env file.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Required ──────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str

    # ── LLM ───────────────────────────────────────────────────────
    MODEL: str = "claude-sonnet-4-6"

    # ── Scraping limits ───────────────────────────────────────────
    MAX_LEADS_PER_SOURCE: int = 50
    MAX_WORKERS: int = 5

    # ── Politeness / rate limiting ────────────────────────────────
    REQUEST_DELAY_MIN: float = 1.5
    REQUEST_DELAY_MAX: float = 4.0

    # ── Output ────────────────────────────────────────────────────
    OUTPUT_DIR: str = "outputs"

    # ── Logging ───────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
