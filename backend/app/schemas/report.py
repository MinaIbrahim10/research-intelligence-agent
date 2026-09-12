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
from app.schemas.verification import (
    VerificationCorpus,
    VerificationStatus,
)


class ReportClaim(BaseModel):

    claim_id: str

    statement: str

    status: VerificationStatus

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    source_ids: list[str]

    caveats: list[str]


class ReportSection(BaseModel):

    question_id: str

    question: str

    # Strength of the claims that exist.
    evidence_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    # How much of the required comparison
    # scope is actually represented.
    coverage_ratio: float = Field(
        ge=0.0,
        le=1.0,
    )

    # Final section confidence after
    # coverage penalty.
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    required_entities: list[str]

    covered_entities: list[str]

    claims: list[
        ReportClaim
    ]

    gaps: list[str]


class ReportSource(BaseModel):

    id: str

    title: str

    url: str

    domain: str

    source_category: str


class ResearchReport(BaseModel):

    title: str

    executive_summary: str

    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    sections: list[
        ReportSection
    ]

    conflicts: list[str]

    gaps: list[str]

    sources: list[
        ReportSource
    ]

    markdown: str


class ReportResponse(BaseModel):

    query: str

    plan: ResearchPlan

    corpus: SearchCorpus

    sources: SourceContentCorpus

    evidence: EvidenceCorpus

    claims: ClaimCorpus

    verification: VerificationCorpus

    report: ResearchReport
