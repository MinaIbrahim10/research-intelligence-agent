from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    app_name: str = (
        "Research & Intelligence Agent"
    )

    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    llm_provider: Literal[
        "ollama",
        "openai_compatible",
    ] = "ollama"

    llm_model: str = "gemma4:e4b"

    llm_base_url: str = (
        "http://localhost:11434"
    )

    llm_api_key: str | None = None

    llm_timeout_seconds: float = 90.0

    searxng_base_url: str = (
        "http://127.0.0.1:8080"
    )

    searxng_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
    )

    search_max_results_per_query: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    source_fetch_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
    )

    source_fetch_max_bytes: int = Field(
        default=1_500_000,
        ge=10_000,
    )

    source_fetch_max_sources_per_question: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
