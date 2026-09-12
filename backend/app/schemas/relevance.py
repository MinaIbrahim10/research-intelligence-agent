from pydantic import (
    BaseModel,
    Field,
)


class EvidenceRelevanceDecision(
    BaseModel
):
    finding_id: str = Field(
        min_length=2,
        max_length=50,
    )

    relevant: bool

    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str = Field(
        min_length=3,
        max_length=300,
    )


class EvidenceRelevanceDraft(
    BaseModel
):
    decisions: list[
        EvidenceRelevanceDecision
    ] = Field(
        default_factory=list,
        max_length=64,
    )
