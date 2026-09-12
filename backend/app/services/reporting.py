from __future__ import annotations

import re

from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.report import (
    ReportClaim,
    ReportSection,
    ReportSource,
    ResearchReport,
)
from app.schemas.search import (
    SearchCorpus,
)
from app.schemas.verification import (
    VerificationCorpus,
    VerifiedClaim,
)


# Captures technical/product names such as:
# LangGraph
# CrewAI
# AutoGen
# GPT-5.5
#
# It deliberately ignores ordinary
# capitalized sentence-start words.
ENTITY_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9.-]*"
    r"[A-Z][A-Za-z0-9.-]*\b"
)


GENERIC_TECH_TERMS = {
    "AI",
    "API",
    "LLM",
    "LLMS",
    "RAG",
    "JSON",
    "HTTP",
    "HTTPS",
}


COMPARISON_CUES = (
    "both ",
    "each framework",
    "each system",
    "each platform",
    "versus",
    " vs ",
    "compare",
    "comparison",
    "between ",
)


class ReportService:

    @staticmethod
    def _unique(
        values: list[str],
    ) -> list[str]:

        result = []
        seen = set()

        for value in values:

            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(value)

        return result

    @classmethod
    def _extract_entities(
        cls,
        text: str,
    ) -> list[str]:

        entities = []

        for match in (
            ENTITY_PATTERN.findall(
                text
            )
        ):

            if (
                match.upper()
                in GENERIC_TECH_TERMS
            ):
                continue

            entities.append(
                match
            )

        return cls._unique(
            entities
        )

    @staticmethod
    def _is_comparative_question(
        question: str,
    ) -> bool:

        normalized = (
            question.casefold()
        )

        return any(
            cue in normalized
            for cue
            in COMPARISON_CUES
        )

    @classmethod
    def _required_entities(
        cls,
        *,
        plan: ResearchPlan,
        question: str,
    ) -> list[str]:

        question_entities = (
            cls._extract_entities(
                question
            )
        )

        # Explicitly named entities in the
        # question are the strongest signal.
        if len(question_entities) >= 2:

            return question_entities

        objective_entities = (
            cls._extract_entities(
                plan.objective
            )
        )

        # Questions like "How does each
        # framework..." inherit the comparison
        # targets from the overall objective.
        if (
            cls._is_comparative_question(
                question
            )
            and len(
                objective_entities
            ) >= 2
        ):

            return objective_entities

        if question_entities:

            return question_entities

        return []

    @staticmethod
    def _claim_mentions_entity(
        claim: str,
        entity: str,
    ) -> bool:

        return (
            entity.casefold()
            in claim.casefold()
        )

    @classmethod
    def _covered_entities(
        cls,
        *,
        required_entities: list[str],
        claims: list[
            VerifiedClaim
        ],
    ) -> list[str]:

        covered = []

        for entity in (
            required_entities
        ):

            if any(
                cls._claim_mentions_entity(
                    claim.claim,
                    entity,
                )
                for claim in claims
                if (
                    claim.status
                    != "UNSUPPORTED"
                )
            ):

                covered.append(
                    entity
                )

        return covered

    @staticmethod
    def _coverage_ratio(
        *,
        required_entities: list[str],
        covered_entities: list[str],
    ) -> float:

        if not required_entities:
            return 1.0

        return round(
            len(covered_entities)
            / len(required_entities),
            3,
        )

    @staticmethod
    def _safe_statement(
        claim: VerifiedClaim,
    ) -> str:

        text = claim.claim.strip()

        if claim.status == "VERIFIED":
            return text

        if (
            claim.status
            == "PARTIALLY_VERIFIED"
        ):
            return (
                "Available evidence supports "
                "this claim, but it is not "
                "independently established: "
                + text
            )

        if claim.status == "CONFLICTING":
            return (
                "Available sources conflict "
                "on the claim: "
                + text
            )

        return (
            "The current research corpus "
            "does not adequately establish "
            "the claim: "
            + text
        )

    @staticmethod
    def _evidence_confidence(
        claims: list[
            VerifiedClaim
        ],
    ) -> float:

        if not claims:
            return 0.0

        return round(
            sum(
                claim.confidence
                for claim in claims
            )
            / len(claims),
            3,
        )

    @staticmethod
    def _section_confidence(
        *,
        evidence_confidence: float,
        coverage_ratio: float,
    ) -> float:

        # High-quality evidence covering only
        # half of a requested comparison is not
        # a high-confidence complete answer.
        return round(
            evidence_confidence
            * coverage_ratio,
            3,
        )

    @staticmethod
    def _overall_confidence(
        sections: list[
            ReportSection
        ],
    ) -> float:

        if not sections:
            return 0.0

        # Equal weight per research question:
        # prevents a heavily researched question
        # from hiding a completely unanswered one.
        return round(
            sum(
                section.confidence
                for section in sections
            )
            / len(sections),
            3,
        )

    @staticmethod
    def _question_gaps(
        *,
        claims: list[
            VerifiedClaim
        ],
        required_entities: list[str],
        covered_entities: list[str],
    ) -> list[str]:

        if not claims:

            gaps = [
                (
                    "No usable verified claims "
                    "were produced for this "
                    "research question."
                )
            ]

        else:

            gaps = []

            if not any(
                claim.status == "VERIFIED"
                for claim in claims
            ):
                gaps.append(
                    (
                        "No claim for this question "
                        "has independent or strong "
                        "first-party verification."
                    )
                )

            if any(
                claim.status
                == "PARTIALLY_VERIFIED"
                for claim in claims
            ):
                gaps.append(
                    (
                        "Some findings still require "
                        "independent corroboration."
                    )
                )

            if any(
                claim.status
                == "CONFLICTING"
                for claim in claims
            ):
                gaps.append(
                    (
                        "Direct source disagreement "
                        "remains unresolved."
                    )
                )

            if any(
                claim.status
                == "UNSUPPORTED"
                for claim in claims
            ):
                gaps.append(
                    (
                        "Some candidate claims lack "
                        "adequate support."
                    )
                )

        missing_entities = [
            entity
            for entity
            in required_entities
            if entity
            not in covered_entities
        ]

        if missing_entities:

            gaps.append(
                (
                    "Comparison coverage is "
                    "missing for: "
                    + ", ".join(
                        missing_entities
                    )
                    + "."
                )
            )

        return gaps

    @staticmethod
    def _build_markdown(
        *,
        title: str,
        executive_summary: str,
        overall_confidence: float,
        sections: list[
            ReportSection
        ],
        conflicts: list[str],
        gaps: list[str],
        sources: list[
            ReportSource
        ],
    ) -> str:

        lines = [
            f"# {title}",
            "",
            executive_summary,
            "",
            (
                "**Overall confidence:** "
                f"{overall_confidence:.2f}"
            ),
            "",
        ]

        for section in sections:

            lines.extend(
                [
                    (
                        "## "
                        + section.question
                    ),
                    "",
                    (
                        "**Evidence confidence:** "
                        f"{section.evidence_confidence:.2f}"
                    ),
                    (
                        "**Coverage:** "
                        f"{section.coverage_ratio:.2f}"
                    ),
                    (
                        "**Section confidence:** "
                        f"{section.confidence:.2f}"
                    ),
                    "",
                ]
            )

            if (
                section.required_entities
            ):

                lines.append(
                    (
                        "**Required coverage:** "
                        + ", ".join(
                            section
                            .required_entities
                        )
                    )
                )

                lines.append(
                    (
                        "**Covered:** "
                        + (
                            ", ".join(
                                section
                                .covered_entities
                            )
                            if (
                                section
                                .covered_entities
                            )
                            else "none"
                        )
                    )
                )

                lines.append("")

            if not section.claims:

                lines.append(
                    (
                        "No sufficiently grounded "
                        "claims were found."
                    )
                )

                lines.append("")

            for claim in section.claims:

                citations = " ".join(
                    f"[{source_id}]"
                    for source_id
                    in claim.source_ids
                )

                line = (
                    "- "
                    + claim.statement
                )

                if citations:
                    line += (
                        " "
                        + citations
                    )

                line += (
                    " — "
                    + claim.status
                    + " "
                    + f"({claim.confidence:.2f})"
                )

                lines.append(
                    line
                )

                for caveat in (
                    claim.caveats
                ):

                    lines.append(
                        (
                            "  - Caveat: "
                            + caveat
                        )
                    )

            if section.gaps:

                lines.extend(
                    [
                        "",
                        "### Evidence gaps",
                        "",
                    ]
                )

                for gap in section.gaps:
                    lines.append(
                        "- " + gap
                    )

            lines.append("")

        if conflicts:

            lines.extend(
                [
                    "## Conflicts",
                    "",
                ]
            )

            for conflict in conflicts:
                lines.append(
                    "- " + conflict
                )

            lines.append("")

        if gaps:

            lines.extend(
                [
                    "## Remaining gaps",
                    "",
                ]
            )

            for gap in gaps:
                lines.append(
                    "- " + gap
                )

            lines.append("")

        lines.extend(
            [
                "## Sources",
                "",
            ]
        )

        for source in sources:

            lines.append(
                (
                    f"- [{source.id}] "
                    f"{source.title} — "
                    f"{source.domain} — "
                    f"{source.url}"
                )
            )

        return "\n".join(
            lines
        ).strip()

    def build(
        self,
        *,
        query: str,
        plan: ResearchPlan,
        corpus: SearchCorpus,
        verification: VerificationCorpus,
    ) -> ResearchReport:

        claims_by_question = {
            question.id: []
            for question
            in plan.questions
        }

        for claim in (
            verification.claims
        ):

            if (
                claim.question_id
                in claims_by_question
            ):
                claims_by_question[
                    claim.question_id
                ].append(
                    claim
                )

        sections = []

        used_source_ids = set()

        for question in plan.questions:

            question_claims = (
                claims_by_question.get(
                    question.id,
                    [],
                )
            )

            question_claims = sorted(
                question_claims,
                key=lambda claim: (
                    {
                        "VERIFIED": 0,
                        "PARTIALLY_VERIFIED": 1,
                        "CONFLICTING": 2,
                        "UNSUPPORTED": 3,
                    }[
                        claim.status
                    ],
                    -claim.confidence,
                ),
            )

            required_entities = (
                self._required_entities(
                    plan=plan,
                    question=(
                        question.question
                    ),
                )
            )

            covered_entities = (
                self._covered_entities(
                    required_entities=(
                        required_entities
                    ),
                    claims=question_claims,
                )
            )

            coverage_ratio = (
                self._coverage_ratio(
                    required_entities=(
                        required_entities
                    ),
                    covered_entities=(
                        covered_entities
                    ),
                )
            )

            evidence_confidence = (
                self._evidence_confidence(
                    question_claims
                )
            )

            section_confidence = (
                self._section_confidence(
                    evidence_confidence=(
                        evidence_confidence
                    ),
                    coverage_ratio=(
                        coverage_ratio
                    ),
                )
            )

            report_claims = []

            # Unsupported candidate claims still
            # influence section gaps/confidence,
            # but should not clutter the final
            # user-facing findings list.
            display_claims = [
                claim
                for claim in question_claims
                if claim.status
                != "UNSUPPORTED"
            ]

            for claim in (
                display_claims
            ):

                for source_id in (
                    claim
                    .supporting_source_ids
                ):
                    used_source_ids.add(
                        source_id
                    )

                for source_id in (
                    claim
                    .contradicting_source_ids
                ):
                    used_source_ids.add(
                        source_id
                    )

                source_ids = []

                for source_id in (
                    claim
                    .supporting_source_ids
                    + claim
                    .contradicting_source_ids
                ):

                    if (
                        source_id
                        not in source_ids
                    ):
                        source_ids.append(
                            source_id
                        )

                report_claims.append(
                    ReportClaim(
                        claim_id=(
                            claim.claim_id
                        ),
                        statement=(
                            self._safe_statement(
                                claim
                            )
                        ),
                        status=(
                            claim.status
                        ),
                        confidence=(
                            claim.confidence
                        ),
                        source_ids=(
                            source_ids
                        ),
                        caveats=(
                            claim.caveats
                        ),
                    )
                )

            section_gaps = (
                self._question_gaps(
                    claims=question_claims,
                    required_entities=(
                        required_entities
                    ),
                    covered_entities=(
                        covered_entities
                    ),
                )
            )

            sections.append(
                ReportSection(
                    question_id=(
                        question.id
                    ),
                    question=(
                        question.question
                    ),
                    evidence_confidence=(
                        evidence_confidence
                    ),
                    coverage_ratio=(
                        coverage_ratio
                    ),
                    confidence=(
                        section_confidence
                    ),
                    required_entities=(
                        required_entities
                    ),
                    covered_entities=(
                        covered_entities
                    ),
                    claims=(
                        report_claims
                    ),
                    gaps=(
                        section_gaps
                    ),
                )
            )

        source_lookup = {
            source.id: source
            for source
            in corpus.results
        }

        report_sources = []

        for source_id in sorted(
            used_source_ids
        ):

            source = source_lookup.get(
                source_id
            )

            if source is None:
                continue

            report_sources.append(
                ReportSource(
                    id=source.id,
                    title=source.title,
                    url=str(
                        source.url
                    ),
                    domain=(
                        source.domain
                    ),
                    source_category=(
                        source
                        .source_category
                    ),
                )
            )

        conflicts = [
            (
                claim.claim
                + " | supporting="
                + ", ".join(
                    claim
                    .supporting_source_ids
                )
                + " | contradicting="
                + ", ".join(
                    claim
                    .contradicting_source_ids
                )
            )
            for claim
            in verification.claims
            if (
                claim.status
                == "CONFLICTING"
            )
        ]

        gaps = []

        for section in sections:

            if section.gaps:

                gaps.append(
                    (
                        section.question_id
                        + ": "
                        + " ".join(
                            section.gaps
                        )
                    )
                )

        total = (
            verification.total_claims
        )

        verified = (
            verification
            .verified_claims
        )

        partial = (
            verification
            .partially_verified_claims
        )

        conflicts_count = (
            verification
            .conflicting_claims
        )

        unsupported = (
            verification
            .unsupported_claims
        )

        overall_confidence = (
            self._overall_confidence(
                sections
            )
        )

        executive_summary = (
            "The research pipeline produced "
            f"{total} consolidated claims: "
            f"{verified} verified, "
            f"{partial} partially verified, "
            f"{conflicts_count} conflicting, "
            f"and {unsupported} unsupported. "
            "Report confidence accounts for "
            "both evidence strength and coverage "
            "of the requested comparison scope."
        )

        title = (
            "Research Report: "
            + query.strip()
        )

        markdown = (
            self._build_markdown(
                title=title,
                executive_summary=(
                    executive_summary
                ),
                overall_confidence=(
                    overall_confidence
                ),
                sections=sections,
                conflicts=conflicts,
                gaps=gaps,
                sources=report_sources,
            )
        )

        return ResearchReport(
            title=title,
            executive_summary=(
                executive_summary
            ),
            overall_confidence=(
                overall_confidence
            ),
            sections=sections,
            conflicts=conflicts,
            gaps=gaps,
            sources=report_sources,
            markdown=markdown,
        )
