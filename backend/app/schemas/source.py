from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.search import SourceCategory


FetchStatus = Literal[
    "fetched",
    "failed",
]


class FetchedSource(BaseModel):
    source_id: str

    title: str

    url: HttpUrl

    final_url: HttpUrl | None = None

    question_ids: list[str] = Field(
        min_length=1,
    )

    source_category: SourceCategory

    final_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    content: str = ""

    content_chars: int = Field(
        ge=0,
    )

    content_type: str | None = None

    status: FetchStatus

    error: str | None = None


class SourceContentCorpus(BaseModel):
    attempted_sources: int = Field(
        ge=0,
    )

    fetched_sources: int = Field(
        ge=0,
    )

    failed_sources: int = Field(
        ge=0,
    )

    results: list[FetchedSource]
