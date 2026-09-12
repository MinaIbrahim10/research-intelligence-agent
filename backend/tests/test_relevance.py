from app.schemas.evidence import (
    EvidenceCorpus,
    EvidenceFinding,
)
from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.relevance import (
    EvidenceRelevanceDecision,
    EvidenceRelevanceDraft,
)
from app.services.relevance import (
    EvidenceRelevanceService,
)


def make_plan():

    return ResearchPlan(
        objective=(
            "Compare LangGraph and CrewAI "
            "for reliable production systems."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How do LangGraph and "
                    "CrewAI manage state?"
                ),
                purpose=(
                    "Compare state management."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How do LangGraph and "
                    "CrewAI recover from failures?"
                ),
                purpose=(
                    "Compare reliability."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "How easy are LangGraph "
                    "and CrewAI to implement?"
                ),
                purpose=(
                    "Compare developer experience."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "official documentation",
            "GitHub repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Frameworks change rapidly."
        ),
        success_criteria=[
            "Compare both frameworks.",
            "Use direct evidence.",
        ],
    )


def make_evidence():

    return EvidenceCorpus(
        total_questions=3,
        total_findings=3,
        findings=[
            EvidenceFinding(
                id="e1",
                question_id="q1",
                claim=(
                    "LangGraph persists workflow "
                    "state using checkpoints."
                ),
                evidence_excerpt=(
                    "LangGraph persists workflow "
                    "state using checkpoints."
                ),
                source_id="s1",
                evidence_type="supporting",
            ),
            EvidenceFinding(
                id="e2",
                question_id="q1",
                claim=(
                    "Microsoft Agent Framework "
                    "provides agent sessions."
                ),
                evidence_excerpt=(
                    "The framework provides an "
                    "agent session."
                ),
                source_id="s2",
                evidence_type="supporting",
            ),
            EvidenceFinding(
                id="e3",
                question_id="q2",
                claim=(
                    "Amazon AgentCore can host "
                    "many agent frameworks."
                ),
                evidence_excerpt=(
                    "AgentCore works with "
                    "multiple frameworks."
                ),
                source_id="s3",
                evidence_type="context",
            ),
        ],
    )


class FakeRelevanceLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return EvidenceRelevanceDraft(
            decisions=[
                EvidenceRelevanceDecision(
                    finding_id="e1",
                    relevant=True,
                    relevance_score=0.95,
                    reason=(
                        "Directly addresses "
                        "LangGraph state."
                    ),
                ),
                EvidenceRelevanceDecision(
                    finding_id="e2",
                    relevant=False,
                    relevance_score=0.10,
                    reason=(
                        "Unrelated framework."
                    ),
                ),
                EvidenceRelevanceDecision(
                    finding_id="e3",
                    relevant=False,
                    relevance_score=0.20,
                    reason=(
                        "Hosting support does not "
                        "answer failure recovery."
                    ),
                ),
            ]
        )


def test_relevance_gate_rejects_topic_drift():

    result = EvidenceRelevanceService(
        FakeRelevanceLLM()
    ).filter(
        make_plan(),
        make_evidence(),
    )

    assert result.total_findings == 1

    assert result.findings[0].id == "e1"


class MissingDecisionLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return EvidenceRelevanceDraft(
            decisions=[]
        )


def test_missing_decisions_fail_closed():

    result = EvidenceRelevanceService(
        MissingDecisionLLM()
    ).filter(
        make_plan(),
        make_evidence(),
    )

    assert result.total_findings == 0


class BatchTrackingRelevanceLLM:

    def __init__(self):
        self.calls = []

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        import json

        marker = (
            "question and its findings."
            "\n\n"
        )

        payload_text = (
            user_prompt.split(
                marker,
                1,
            )[1]
        )

        payload = json.loads(
            payload_text
        )

        findings = payload[
            "findings"
        ]

        self.calls.append(
            {
                "question_id": (
                    payload[
                        "question"
                    ]["id"]
                ),
                "finding_count": len(
                    findings
                ),
            }
        )

        return EvidenceRelevanceDraft(
            decisions=[
                EvidenceRelevanceDecision(
                    finding_id=item["id"],
                    relevant=True,
                    relevance_score=0.90,
                    reason="Directly relevant.",
                )
                for item in findings
            ]
        )


def test_relevance_is_batched_per_question():

    llm = BatchTrackingRelevanceLLM()

    result = EvidenceRelevanceService(
        llm
    ).filter(
        make_plan(),
        make_evidence(),
    )

    assert result.total_findings == 3

    assert len(llm.calls) == 2

    assert llm.calls[0] == {
        "question_id": "q1",
        "finding_count": 2,
    }

    assert llm.calls[1] == {
        "question_id": "q2",
        "finding_count": 1,
    }

    assert all(
        call["finding_count"] <= 4
        for call in llm.calls
    )
