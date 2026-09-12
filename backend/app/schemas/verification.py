from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.claims import (
    ClaimCorpus,
)
from app.schemas.evidence import (
    EvidenceCorpus,
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


VerificationStatus = Literal[
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "CONFLICTING",
    "UNSUPPORTED",
]


class VerificationDecision(BaseModel):

    claim_id: str = Field(
        min_length=2,
        max_length=50,
    )

    status: VerificationStatus

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    supporting_source_ids: list[str] = Field(
        default_factory=list,
        max_length=12,
    )

    contradicting_source_ids: list[str] = Field(
        default_factory=list,
        max_length=12,
    )

    rationale: str = Field(
        min_length=3,
        max_length=500,
    )

    caveats: list[str] = Field(
        default_factory=list,
        max_length=4,
    )


class QuestionVerificationDraft(
    BaseModel
):

    question_id: str = Field(
        min_length=2,
        max_length=50,
    )

    decisions: list[
        VerificationDecision
    ] = Field(
        default_factory=list,
        max_length=4,
    )


class VerifiedClaim(BaseModel):

    claim_id: str

    question_id: str

    claim: str

    finding_ids: list[str]

    status: VerificationStatus

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    supporting_source_ids: list[str]

    contradicting_source_ids: list[str]

    rationale: str

    caveats: list[str]


class VerificationCorpus(BaseModel):

    total_claims: int = Field(
        ge=0,
    )

    verified_claims: int = Field(
        ge=0,
    )

    partially_verified_claims: int = Field(
        ge=0,
    )

    conflicting_claims: int = Field(
        ge=0,
    )

    unsupported_claims: int = Field(
        ge=0,
    )

    claims: list[
        VerifiedClaim
    ]


class VerificationResponse(BaseModel):

    query: str

    plan: ResearchPlan

    corpus: SearchCorpus

    sources: SourceContentCorpus

    evidence: EvidenceCorpus

    claims: ClaimCorpus

    verification: VerificationCorpus
