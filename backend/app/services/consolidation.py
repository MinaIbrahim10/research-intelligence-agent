from __future__ import annotations

import json

from app.providers.base import (
    StructuredLLM,
)
from app.schemas.claims import (
    ClaimCorpus,
    ClaimEvidenceMember,
    ConsolidatedClaim,
    QuestionClaimDraft,
)
from app.schemas.evidence import (
    EvidenceCorpus,
    EvidenceFinding,
)
from app.schemas.planner import (
    ResearchPlan,
)


CONSOLIDATION_SYSTEM_PROMPT = """
You are the Claim Consolidation Agent in an
evidence-first research system.

Your ONLY task is to group evidence findings
that express substantially the same factual
claim.

You do NOT verify truth.
You do NOT create new claims.
You do NOT use outside knowledge.

STRICT RULES:

1. Group findings only when they make the same
   underlying factual assertion.

2. Findings merely about the same general topic
   must NOT be grouped.

3. A broad claim and a narrow claim should stay
   separate unless they are genuinely equivalent.

4. Quantitative benchmark claims must stay
   separate from qualitative claims.

5. Evaluative recommendations such as
   "best", "better", "ideal", or "recommended"
   must not be grouped with factual capability
   claims unless both findings make the same
   evaluative assertion.

6. Never invent finding IDs.

6. Every supplied finding should appear in at
   most one group.

7. Groups may contain one or more findings.

8. Return only structured JSON.
""".strip()


EVALUATIVE_TERMS = (
    "best",
    "better",
    "worse",
    "strongest",
    "recommended",
    "recommend ",
    "ideal",
    "easiest",
    "harder",
    "faster",
    "slower",
    "cheaper",
)


def _is_evaluative_claim(
    claim: str,
) -> bool:

    normalized = claim.casefold()

    return any(
        term in normalized
        for term in EVALUATIVE_TERMS
    )


class ClaimConsolidationService:

    def __init__(
        self,
        llm: StructuredLLM,
    ) -> None:

        self.llm = llm

    @staticmethod
    def _make_claim(
        *,
        claim_id: str,
        question_id: str,
        findings: list[
            EvidenceFinding
        ],
    ) -> ConsolidatedClaim:

        # IMPORTANT:
        # canonical wording comes from an
        # existing grounded finding.
        canonical = findings[0].claim

        source_ids = []

        for finding in findings:

            if (
                finding.source_id
                not in source_ids
            ):
                source_ids.append(
                    finding.source_id
                )

        members = [
            ClaimEvidenceMember(
                finding_id=finding.id,
                source_id=(
                    finding.source_id
                ),
                claim=finding.claim,
                evidence_excerpt=(
                    finding.evidence_excerpt
                ),
                evidence_type=(
                    finding.evidence_type
                ),
            )
            for finding in findings
        ]

        return ConsolidatedClaim(
            id=claim_id,
            question_id=question_id,
            claim=canonical,
            finding_ids=[
                finding.id
                for finding in findings
            ],
            source_ids=source_ids,
            members=members,
        )

    def consolidate(
        self,
        plan: ResearchPlan,
        evidence: EvidenceCorpus,
    ) -> ClaimCorpus:

        findings_by_question = {
            question.id: []
            for question
            in plan.questions
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

        claims: list[
            ConsolidatedClaim
        ] = []

        for question in plan.questions:

            question_findings = (
                findings_by_question.get(
                    question.id,
                    [],
                )
            )[:4]

            if not question_findings:
                continue

            finding_lookup = {
                finding.id: finding
                for finding
                in question_findings
            }

            payload = {
                "research_question": {
                    "id": question.id,
                    "question": (
                        question.question
                    ),
                },
                "findings": [
                    {
                        "id": finding.id,
                        "claim": (
                            finding.claim
                        ),
                        "source_id": (
                            finding.source_id
                        ),
                        "evidence_type": (
                            finding.evidence_type
                        ),
                    }
                    for finding
                    in question_findings
                ],
            }

            groups: list[
                list[
                    EvidenceFinding
                ]
            ] = []

            assigned: set[str] = set()

            try:

                draft = (
                    self.llm
                    .generate_structured(
                        system_prompt=(
                            CONSOLIDATION_SYSTEM_PROMPT
                        ),
                        user_prompt=(
                            "Group equivalent "
                            "findings for this "
                            "single question.\n\n"
                            + json.dumps(
                                payload,
                                ensure_ascii=False,
                                indent=2,
                            )
                        ),
                        schema=(
                            QuestionClaimDraft
                        ),
                    )
                )

            except Exception:

                draft = None

            if (
                draft is not None
                and draft.question_id
                == question.id
            ):

                for candidate in (
                    draft.groups
                ):

                    valid_ids = []

                    for finding_id in (
                        candidate.finding_ids
                    ):

                        if (
                            finding_id
                            not in finding_lookup
                        ):
                            continue

                        if (
                            finding_id
                            in assigned
                        ):
                            continue

                        if (
                            finding_id
                            in valid_ids
                        ):
                            continue

                        valid_ids.append(
                            finding_id
                        )

                    if not valid_ids:
                        continue

                    grouped = [
                        finding_lookup[
                            finding_id
                        ]
                        for finding_id
                        in valid_ids
                    ]

                    evaluation_flags = {
                        _is_evaluative_claim(
                            finding.claim
                        )
                        for finding
                        in grouped
                    }

                    # Never let an LLM merge a
                    # recommendation/opinion with
                    # a factual capability claim.
                    if len(
                        evaluation_flags
                    ) > 1:

                        for finding in grouped:

                            groups.append(
                                [finding]
                            )

                            assigned.add(
                                finding.id
                            )

                        continue

                    groups.append(
                        grouped
                    )

                    assigned.update(
                        valid_ids
                    )

            # Fail-safe:
            # anything omitted by the model
            # becomes its own grounded claim.
            for finding in (
                question_findings
            ):

                if finding.id in assigned:
                    continue

                groups.append(
                    [finding]
                )

                assigned.add(
                    finding.id
                )

            for grouped_findings in groups:

                claims.append(
                    self._make_claim(
                        claim_id=f"c{len(claims) + 1}",
                        question_id=(
                            question.id
                        ),
                        findings=(
                            grouped_findings
                        ),
                    )
                )

        return ClaimCorpus(
            total_claims=len(
                claims
            ),
            claims=claims,
        )
