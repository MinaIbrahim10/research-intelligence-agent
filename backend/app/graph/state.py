from typing import TypedDict

from app.schemas.claims import (
    ClaimCorpus,
)
from app.schemas.evidence import (
    EvidenceCorpus,
)
from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.report import (
    ResearchReport,
)
from app.schemas.search import (
    SearchCorpus,
)
from app.schemas.source import (
    SourceContentCorpus,
)
from app.schemas.verification import (
    VerificationCorpus,
)


class ResearchState(
    TypedDict,
    total=False,
):
    query: str

    plan: ResearchPlan

    corpus: SearchCorpus

    source_corpus: SourceContentCorpus

    raw_evidence: EvidenceCorpus

    evidence: EvidenceCorpus

    claims: ClaimCorpus

    verification: VerificationCorpus

    report: ResearchReport

    errors: list[str]
