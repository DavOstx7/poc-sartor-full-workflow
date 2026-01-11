"""
Configuration management for Sartor Ad Engine.

Uses pydantic-settings for type-safe environment variable loading.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables can be set directly or via a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === LLM API Keys ===
    google_api_key: str = ""
    anthropic_api_key: str = ""

    # === Image Generation ===
    imagen_api_key: str = ""

    # === Model Names (configurable per agent) ===
    segmentation_model: str = "gemini-2.0-flash-thinking-exp"
    strategy_model: str = "gemini-2.0-pro"
    concept_model: str = "claude-sonnet-4-20250514"
    copy_model: str = "gemini-2.0-flash"
    design_model: str = "imagen-3"  # Image generation model

    # === Paths ===
    output_dir: Path = Path("output")
    assets_dir: Path = Path("assets")
    data_dir: Path = Path("data")

    # === Pipeline Settings ===
    max_icps: int = 4  # Maximum ICPs from segmentation
    llm_rate_limit_rpm: float = 5.0  # Requests per minute (0 = disabled)

    # === Debug Settings ===
    debug: bool = False
    log_prompts: bool = False


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Convenience function to access settings
settings = get_settings()
