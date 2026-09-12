from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.search import (
    SearchCorpus,
)
from app.schemas.source import (
    SourceContentCorpus,
)


EvidenceType = Literal[
    "supporting",
    "contradicting",
    "context",
]


class EvidenceCandidate(BaseModel):
    claim: str = Field(
        min_length=8,
        max_length=800,
    )

    evidence_excerpt: str = Field(
        min_length=5,
        max_length=1200,
    )

    source_id: str = Field(
        min_length=2,
        max_length=50,
    )

    evidence_type: EvidenceType


class QuestionEvidenceDraft(BaseModel):
    question_id: str = Field(
        min_length=2,
        max_length=50,
    )

    findings: list[
        EvidenceCandidate
    ] = Field(
        default_factory=list,
        max_length=4,
    )


class EvidenceFinding(BaseModel):
    id: str

    question_id: str

    claim: str

    evidence_excerpt: str

    source_id: str

    evidence_type: EvidenceType


class EvidenceCorpus(BaseModel):
    total_questions: int = Field(
        ge=1,
    )

    total_findings: int = Field(
        ge=0,
    )

    findings: list[
        EvidenceFinding
    ]


class EvidenceResponse(BaseModel):
    query: str

    plan: ResearchPlan

    corpus: SearchCorpus

    sources: SourceContentCorpus

    evidence: EvidenceCorpus
