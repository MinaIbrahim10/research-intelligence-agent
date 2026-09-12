from pydantic import (
    BaseModel,
    Field,
)


class ClaimGroupCandidate(BaseModel):

    finding_ids: list[str] = Field(
        min_length=1,
        max_length=4,
    )


class QuestionClaimDraft(BaseModel):

    question_id: str = Field(
        min_length=2,
        max_length=50,
    )

    groups: list[
        ClaimGroupCandidate
    ] = Field(
        default_factory=list,
        max_length=4,
    )


class ClaimEvidenceMember(BaseModel):

    finding_id: str

    source_id: str

    claim: str

    evidence_excerpt: str

    evidence_type: str


class ConsolidatedClaim(BaseModel):

    id: str

    question_id: str

    claim: str

    finding_ids: list[str] = Field(
        min_length=1,
        max_length=4,
    )

    source_ids: list[str] = Field(
        min_length=1,
        max_length=4,
    )

    members: list[
        ClaimEvidenceMember
    ] = Field(
        min_length=1,
        max_length=4,
    )


class ClaimCorpus(BaseModel):

    total_claims: int = Field(
        ge=0,
    )

    claims: list[
        ConsolidatedClaim
    ]
