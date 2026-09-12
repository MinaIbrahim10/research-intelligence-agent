from __future__ import annotations

import json

from app.providers.base import (
    StructuredLLM,
)
from app.schemas.evidence import (
    EvidenceCorpus,
)
from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.relevance import (
    EvidenceRelevanceDraft,
)


RELEVANCE_SYSTEM_PROMPT = """
You are the Evidence Relevance Gate in an
evidence-first research system.

You do NOT determine whether a claim is true.
A later Verification Agent does that.

Your only task is to determine whether each
evidence finding directly helps answer the
specific research question supplied to you.

STRICT RULES:

1. Judge relevance to the exact research
   question, not merely the broad topic.

2. A claim about an unrelated framework,
   platform, vendor, product, or technology
   must be rejected unless the question
   explicitly asks about it.

3. Generic statements about AI agents or
   orchestration must be rejected when the
   question asks about named frameworks.

4. Third-party infrastructure merely
   supporting both target frameworks does
   NOT establish differences between them.

5. Marketing, benchmark, and performance
   claims may pass relevance only if they
   directly address the question.
   Truth is checked later.

6. relevant=true requires relevance_score
   >= 0.70.

7. Never invent finding IDs.

8. Return exactly one decision for every
   supplied finding.

9. Keep each reason concise and specific,
   preferably under 120 characters.

Return structured JSON only.
""".strip()


class EvidenceRelevanceService:

    def __init__(
        self,
        llm: StructuredLLM,
        *,
        acceptance_threshold: float = 0.70,
    ) -> None:

        if not (
            0.0
            <= acceptance_threshold
            <= 1.0
        ):
            raise ValueError(
                "acceptance_threshold must "
                "be between 0 and 1"
            )

        self.llm = llm

        self.acceptance_threshold = (
            acceptance_threshold
        )

    def filter(
        self,
        plan: ResearchPlan,
        evidence: EvidenceCorpus,
    ) -> EvidenceCorpus:

        if not evidence.findings:

            return EvidenceCorpus(
                total_questions=(
                    evidence.total_questions
                ),
                total_findings=0,
                findings=[],
            )

        findings_by_question = {
            question.id: []
            for question in plan.questions
        }

        for finding in evidence.findings:

            if (
                finding.question_id
                in findings_by_question
            ):
                findings_by_question[
                    finding.question_id
                ].append(
                    finding
                )

        accepted_ids: set[str] = set()

        for question in plan.questions:

            question_findings = (
                findings_by_question.get(
                    question.id,
                    [],
                )
            )

            if not question_findings:
                continue

            # Research extraction already limits
            # each question to at most 4 findings.
            # Keep this additional guard here so
            # relevance prompts remain bounded
            # even if upstream limits change.
            question_findings = (
                question_findings[:4]
            )

            payload = {
                "research_objective": (
                    plan.objective
                ),
                "question": {
                    "id": question.id,
                    "question": (
                        question.question
                    ),
                    "purpose": (
                        question.purpose
                    ),
                },
                "findings": [
                    {
                        "id": finding.id,
                        "claim": (
                            finding.claim
                        ),
                        "evidence_excerpt": (
                            finding
                            .evidence_excerpt
                        ),
                        "source_id": (
                            finding.source_id
                        ),
                        "evidence_type": (
                            finding
                            .evidence_type
                        ),
                    }
                    for finding
                    in question_findings
                ],
            }

            draft = (
                self.llm.generate_structured(
                    system_prompt=(
                        RELEVANCE_SYSTEM_PROMPT
                    ),
                    user_prompt=(
                        "Evaluate relevance for "
                        "this single research "
                        "question and its findings."
                        "\n\n"
                        + json.dumps(
                            payload,
                            ensure_ascii=False,
                            indent=2,
                        )
                    ),
                    schema=(
                        EvidenceRelevanceDraft
                    ),
                )
            )

            valid_ids = {
                finding.id
                for finding
                in question_findings
            }

            decisions = {}

            for decision in (
                draft.decisions
            ):

                if (
                    decision.finding_id
                    not in valid_ids
                ):
                    continue

                decisions[
                    decision.finding_id
                ] = decision

            for finding in (
                question_findings
            ):

                decision = decisions.get(
                    finding.id
                )

                # Fail closed:
                # missing decision means evidence
                # does not pass the relevance gate.
                if decision is None:
                    continue

                if not decision.relevant:
                    continue

                if (
                    decision.relevance_score
                    < self.acceptance_threshold
                ):
                    continue

                accepted_ids.add(
                    finding.id
                )

        # Preserve original evidence ordering.
        accepted = [
            finding
            for finding in evidence.findings
            if finding.id in accepted_ids
        ]

        return EvidenceCorpus(
            total_questions=(
                evidence.total_questions
            ),
            total_findings=len(
                accepted
            ),
            findings=accepted,
        )
