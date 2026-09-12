from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ResearchQuestion(BaseModel):
    id: str = Field(description="Stable short identifier such as q1, q2, q3")
    question: str = Field(min_length=8, max_length=400)
    purpose: str = Field(min_length=5, max_length=300)
    priority: Literal["high", "medium", "low"] = "medium"


class ResearchPlan(BaseModel):
    objective: str = Field(min_length=10, max_length=600)
    questions: list[ResearchQuestion] = Field(min_length=3, max_length=8)
    suggested_source_types: list[str] = Field(min_length=2, max_length=8)
    freshness_required: bool
    freshness_reason: str = Field(min_length=5, max_length=300)
    success_criteria: list[str] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def ensure_unique_questions(self):
        ids = [item.id.strip().lower() for item in self.questions]
        texts = [" ".join(item.question.lower().split()) for item in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Research question ids must be unique")
        if len(texts) != len(set(texts)):
            raise ValueError("Research questions must be unique")
        return self

    @field_validator("suggested_source_types", "success_criteria")
    @classmethod
    def strip_and_dedupe(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            item = item.strip()
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned


class PlanRequest(BaseModel):
    query: str = Field(min_length=8, max_length=1500)


class PlanResponse(BaseModel):
    query: str
    plan: ResearchPlan
