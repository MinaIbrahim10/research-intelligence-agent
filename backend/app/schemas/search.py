from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.planner import ResearchPlan


SourceCategory = Literal[
    "government",
    "academic",
    "documentation",
    "repository",
    "news",
    "general_web",
]


class SearchResult(BaseModel):
    id: str

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    url: HttpUrl

    content: str = Field(
        default="",
        max_length=5000,
    )

    domain: str

    source_category: SourceCategory = (
        "general_web"
    )

    provider_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    authority_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    final_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    published_date: str | None = None

    engine: str | None = None

    question_ids: list[str] = Field(
        min_length=1
    )


class SearchCorpus(BaseModel):
    total_queries: int = Field(
        ge=1
    )

    unique_sources: int = Field(
        ge=0
    )

    results: list[SearchResult]


class SearchResponse(BaseModel):
    query: str
    plan: ResearchPlan
    corpus: SearchCorpus
