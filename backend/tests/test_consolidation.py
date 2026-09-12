from app.schemas.claims import (
    ClaimGroupCandidate,
    QuestionClaimDraft,
)
from app.schemas.evidence import (
    EvidenceCorpus,
    EvidenceFinding,
)
from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.services.consolidation import (
    ClaimConsolidationService,
)


def make_plan():

    return ResearchPlan(
        objective=(
            "Compare LangGraph and CrewAI."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How does LangGraph "
                    "represent workflows?"
                ),
                purpose=(
                    "Compare architecture."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How is persistence handled?"
                ),
                purpose=(
                    "Compare persistence."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "How are tools integrated?"
                ),
                purpose=(
                    "Compare integration."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "official documentation",
            "repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Frameworks change."
        ),
        success_criteria=[
            "Use evidence.",
            "Compare frameworks.",
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
                    "LangGraph uses explicit "
                    "state graphs."
                ),
                evidence_excerpt=(
                    "LangGraph uses explicit "
                    "state graphs."
                ),
                source_id="s1",
                evidence_type="supporting",
            ),
            EvidenceFinding(
                id="e2",
                question_id="q1",
                claim=(
                    "LangGraph exposes stateful "
                    "graph workflow control."
                ),
                evidence_excerpt=(
                    "LangGraph exposes stateful "
                    "graph workflow control."
                ),
                source_id="s2",
                evidence_type="supporting",
            ),
            EvidenceFinding(
                id="e3",
                question_id="q1",
                claim=(
                    "CrewAI uses role-based "
                    "agent teams."
                ),
                evidence_excerpt=(
                    "CrewAI uses role-based "
                    "agent teams."
                ),
                source_id="s3",
                evidence_type="supporting",
            ),
        ],
    )


class FakeConsolidationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionClaimDraft(
            question_id="q1",
            groups=[
                ClaimGroupCandidate(
                    finding_ids=[
                        "e1",
                        "e2",
                    ]
                ),
                ClaimGroupCandidate(
                    finding_ids=[
                        "e3",
                    ]
                ),
            ],
        )


def test_equivalent_findings_are_consolidated():

    result = ClaimConsolidationService(
        FakeConsolidationLLM()
    ).consolidate(
        make_plan(),
        make_evidence(),
    )

    assert result.total_claims == 2

    first = result.claims[0]

    assert first.finding_ids == [
        "e1",
        "e2",
    ]

    assert first.source_ids == [
        "s1",
        "s2",
    ]

    # Canonical wording must come from
    # existing evidence, not invented text.
    assert first.claim == (
        "LangGraph uses explicit "
        "state graphs."
    )


class BrokenConsolidationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):
        raise RuntimeError(
            "model failed"
        )


def test_consolidation_failure_falls_back_to_singletons():

    result = ClaimConsolidationService(
        BrokenConsolidationLLM()
    ).consolidate(
        make_plan(),
        make_evidence(),
    )

    assert result.total_claims == 3

    assert all(
        len(claim.finding_ids) == 1
        for claim in result.claims
    )


class OverMergingConsolidationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionClaimDraft(
            question_id="q1",
            groups=[
                ClaimGroupCandidate(
                    finding_ids=[
                        "e1",
                        "e2",
                    ]
                )
            ],
        )


def test_evaluative_and_factual_claims_are_not_merged():

    evidence = EvidenceCorpus(
        total_questions=3,
        total_findings=2,
        findings=[
            EvidenceFinding(
                id="e1",
                question_id="q1",
                claim=(
                    "LangGraph supports "
                    "stateful graph control."
                ),
                evidence_excerpt=(
                    "LangGraph supports "
                    "stateful graph control."
                ),
                source_id="s1",
                evidence_type="supporting",
            ),
            EvidenceFinding(
                id="e2",
                question_id="q1",
                claim=(
                    "LangGraph is best for "
                    "complex workflows."
                ),
                evidence_excerpt=(
                    "LangGraph is best for "
                    "complex workflows."
                ),
                source_id="s2",
                evidence_type="supporting",
            ),
        ],
    )

    result = ClaimConsolidationService(
        OverMergingConsolidationLLM()
    ).consolidate(
        make_plan(),
        evidence,
    )

    assert result.total_claims == 2

    assert all(
        len(claim.finding_ids) == 1
        for claim in result.claims
    )
