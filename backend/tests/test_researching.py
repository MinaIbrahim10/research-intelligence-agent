from app.schemas.evidence import (
    EvidenceCandidate,
    QuestionEvidenceDraft,
)
from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.source import (
    FetchedSource,
    SourceContentCorpus,
)
from app.services.researching import (
    ResearchService,
)


def make_plan():

    return ResearchPlan(
        objective=(
            "Evaluate production agent "
            "framework capabilities."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How is state persisted "
                    "in production workflows?"
                ),
                purpose="Evaluate persistence.",
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How are failures handled?"
                ),
                purpose="Evaluate reliability.",
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "What observability "
                    "capabilities exist?"
                ),
                purpose="Evaluate operations.",
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "official documentation",
            "official repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Framework APIs change often."
        ),
        success_criteria=[
            "Use direct evidence.",
            "Record unsupported areas.",
        ],
    )


def make_sources():

    contents = {
        "s1": (
            "The runtime uses durable "
            "checkpoints to persist "
            "workflow state."
        ),
        "s2": (
            "Failed tasks can be retried "
            "from the last saved state."
        ),
        "s3": (
            "Execution traces record "
            "node transitions and tool calls."
        ),
    }

    results = []

    for index in range(
        1,
        4,
    ):
        source_id = (
            f"s{index}"
        )

        content = contents[
            source_id
        ]

        results.append(
            FetchedSource(
                source_id=source_id,
                title=f"Source {index}",
                url=(
                    "https://docs.example.com/"
                    f"{source_id}"
                ),
                final_url=(
                    "https://docs.example.com/"
                    f"{source_id}"
                ),
                question_ids=[
                    f"q{index}"
                ],
                source_category=(
                    "documentation"
                ),
                final_score=0.95,
                content=content,
                content_chars=len(
                    content
                ),
                content_type="text/html",
                status="fetched",
            )
        )

    return SourceContentCorpus(
        attempted_sources=3,
        fetched_sources=3,
        failed_sources=0,
        results=results,
    )


class FakeEvidenceLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        if "q1" in user_prompt:
            return QuestionEvidenceDraft(
                question_id="q1",
                findings=[
                    EvidenceCandidate(
                        claim=(
                            "Workflow state can "
                            "be persisted."
                        ),
                        evidence_excerpt=(
                            "The runtime uses durable "
                            "checkpoints to persist "
                            "workflow state."
                        ),
                        source_id="s1",
                        evidence_type="supporting",
                    )
                ],
            )

        if "q2" in user_prompt:
            return QuestionEvidenceDraft(
                question_id="q2",
                findings=[
                    EvidenceCandidate(
                        claim=(
                            "Failed tasks can retry "
                            "from saved state."
                        ),
                        evidence_excerpt=(
                            "Failed tasks can be retried "
                            "from the last saved state."
                        ),
                        source_id="s2",
                        evidence_type="supporting",
                    )
                ],
            )

        return QuestionEvidenceDraft(
            question_id="q3",
            findings=[
                EvidenceCandidate(
                    claim=(
                        "Execution tracing records "
                        "workflow activity."
                    ),
                    evidence_excerpt=(
                        "Execution traces record "
                        "node transitions and tool calls."
                    ),
                    source_id="s3",
                    evidence_type="supporting",
                )
            ],
        )


class HallucinatingEvidenceLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        question_id = (
            "q1"
            if "q1" in user_prompt
            else "q2"
            if "q2" in user_prompt
            else "q3"
        )

        return QuestionEvidenceDraft(
            question_id=question_id,
            findings=[
                EvidenceCandidate(
                    claim=(
                        "Invented unsupported claim."
                    ),
                    evidence_excerpt=(
                        "This sentence does not "
                        "exist in the source."
                    ),
                    source_id="s999",
                    evidence_type="supporting",
                )
            ],
        )


def test_research_service_extracts_traceable_evidence():

    result = ResearchService(
        FakeEvidenceLLM()
    ).extract_evidence(
        make_plan(),
        make_sources(),
    )

    assert result.total_questions == 3
    assert result.total_findings == 3

    assert [
        item.source_id
        for item in result.findings
    ] == [
        "s1",
        "s2",
        "s3",
    ]


def test_research_service_rejects_hallucinated_sources():

    result = ResearchService(
        HallucinatingEvidenceLLM()
    ).extract_evidence(
        make_plan(),
        make_sources(),
    )

    assert result.total_findings == 0


def test_question_evidence_draft_limits_findings():

    import pytest
    from pydantic import ValidationError

    from app.schemas.evidence import (
        EvidenceCandidate,
        QuestionEvidenceDraft,
    )

    findings = [
        EvidenceCandidate(
            claim=(
                f"Supported technical claim {i}."
            ),
            evidence_excerpt=(
                f"Direct evidence excerpt {i}."
            ),
            source_id="s1",
            evidence_type="supporting",
        )
        for i in range(5)
    ]

    with pytest.raises(
        ValidationError
    ):
        QuestionEvidenceDraft(
            question_id="q1",
            findings=findings,
        )
