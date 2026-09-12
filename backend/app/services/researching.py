from __future__ import annotations

import json

from app.providers.base import (
    StructuredLLM,
)
from app.schemas.evidence import (
    EvidenceCorpus,
    EvidenceFinding,
    QuestionEvidenceDraft,
)
from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.source import (
    SourceContentCorpus,
)


RESEARCH_SYSTEM_PROMPT = """
You are the Evidence Extraction Agent in an
evidence-first research system.

Your task is NOT to answer the user's overall
research question.

Your task is to extract atomic claims supported
by the supplied full-page source text.

STRICT RULES:

1. Use ONLY the supplied source content.
2. Do not use outside knowledge.
3. Never invent a source ID.
4. evidence_excerpt must be copied directly
   from the supplied source content.
5. Each finding must contain one clear claim.
6. A finding may be supporting,
   contradicting, or context.
7. If no useful evidence exists, return an
   empty findings list.
8. Never infer a fact that is not explicitly
   supported by the text.
9. Prefer concrete technical facts over
   marketing language or vague opinions.
10. Avoid extracting claims from calls to
    action, promotional language, or generic
    descriptions.
11. Return at most 4 findings.
12. Prefer the 4 strongest and most directly
    relevant findings.
13. Keep each evidence excerpt concise:
    ideally 1-3 sentences and under 600
    characters.
14. Do not repeat substantially similar claims.
15. Return only data matching the supplied
    JSON schema.
""".strip()


def _normalize_text(
    value: str,
) -> str:

    return " ".join(
        value.strip().split()
    ).casefold()


class ResearchService:

    def __init__(
        self,
        llm: StructuredLLM,
        *,
        max_sources_per_question: int = 3,
        max_chars_per_source: int = 2800,
    ) -> None:

        if max_sources_per_question < 1:
            raise ValueError(
                "max_sources_per_question "
                "must be at least 1"
            )

        if max_chars_per_source < 500:
            raise ValueError(
                "max_chars_per_source "
                "must be at least 500"
            )

        self.llm = llm

        self.max_sources_per_question = (
            max_sources_per_question
        )

        self.max_chars_per_source = (
            max_chars_per_source
        )

    def extract_evidence(
        self,
        plan: ResearchPlan,
        source_corpus: SourceContentCorpus,
    ) -> EvidenceCorpus:

        source_lookup = {
            source.source_id: source
            for source
            in source_corpus.results
            if source.status == "fetched"
        }

        findings: list[
            EvidenceFinding
        ] = []

        seen: set[
            tuple[str, str]
        ] = set()

        for question in plan.questions:

            relevant_sources = [
                source
                for source
                in source_corpus.results
                if (
                    source.status
                    == "fetched"
                    and question.id
                    in source.question_ids
                    and source.content.strip()
                )
            ]

            relevant_sources.sort(
                key=lambda source: (
                    source.final_score
                ),
                reverse=True,
            )

            relevant_sources = (
                relevant_sources[
                    :self.max_sources_per_question
                ]
            )

            if not relevant_sources:
                continue

            source_payload = []

            for source in relevant_sources:

                source_payload.append(
                    {
                        "id": (
                            source.source_id
                        ),
                        "title": (
                            source.title
                        ),
                        "url": str(
                            source.final_url
                            or source.url
                        ),
                        "source_category": (
                            source.source_category
                        ),
                        "final_score": (
                            source.final_score
                        ),
                        "content": (
                            source.content[
                                :self.max_chars_per_source
                            ]
                        ),
                    }
                )

            user_prompt = (
                f"Research question ID: "
                f"{question.id}\n\n"
                f"Research question:\n"
                f"{question.question}\n\n"
                f"Purpose:\n"
                f"{question.purpose}\n\n"
                f"Full-page sources:\n"
                f"{json.dumps(
                    source_payload,
                    ensure_ascii=False,
                    indent=2,
                )}"
            )

            draft = (
                self.llm.generate_structured(
                    system_prompt=(
                        RESEARCH_SYSTEM_PROMPT
                    ),
                    user_prompt=user_prompt,
                    schema=(
                        QuestionEvidenceDraft
                    ),
                )
            )

            if (
                draft.question_id
                != question.id
            ):
                continue

            allowed_source_ids = {
                source.source_id
                for source
                in relevant_sources
            }

            for candidate in (
                draft.findings[:4]
            ):

                if (
                    candidate.source_id
                    not in allowed_source_ids
                ):
                    continue

                source = source_lookup[
                    candidate.source_id
                ]

                normalized_excerpt = (
                    _normalize_text(
                        candidate.evidence_excerpt
                    )
                )

                normalized_source = (
                    _normalize_text(
                        source.content[
                            :self.max_chars_per_source
                        ]
                    )
                )

                if (
                    not normalized_excerpt
                    or normalized_excerpt
                    not in normalized_source
                ):
                    continue

                dedupe_key = (
                    candidate.source_id,
                    _normalize_text(
                        candidate.claim
                    ),
                )

                if (
                    dedupe_key
                    in seen
                ):
                    continue

                seen.add(
                    dedupe_key
                )

                findings.append(
                    EvidenceFinding(
                        id=f"e{len(findings) + 1}",
                        question_id=(
                            question.id
                        ),
                        claim=(
                            candidate.claim
                        ),
                        evidence_excerpt=(
                            candidate.evidence_excerpt
                        ),
                        source_id=(
                            candidate.source_id
                        ),
                        evidence_type=(
                            candidate.evidence_type
                        ),
                    )
                )

        return EvidenceCorpus(
            total_questions=len(
                plan.questions
            ),
            total_findings=len(
                findings
            ),
            findings=findings,
        )
