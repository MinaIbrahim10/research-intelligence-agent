from __future__ import annotations

import json
import re

from app.providers.base import (
    StructuredLLM,
)
from app.schemas.claims import (
    ClaimCorpus,
    ConsolidatedClaim,
)
from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.schemas.source import (
    SourceContentCorpus,
)
from app.schemas.verification import (
    QuestionVerificationDraft,
    VerificationCorpus,
    VerificationStatus,
    VerifiedClaim,
)


VERIFICATION_SYSTEM_PROMPT = """
You are the Verification Agent in an
evidence-first research system.

You receive consolidated claims with their
grounded evidence members.

You must use ONLY the supplied evidence.

Do NOT perform new research.
Do NOT use outside knowledge.

STATUSES:

VERIFIED:
Strong direct support with appropriate
corroboration.

PARTIALLY_VERIFIED:
Supported, but evidence is limited,
source-dependent, incomplete, or lacks
independent corroboration.

CONFLICTING:
Supplied sources directly disagree.

UNSUPPORTED:
Evidence does not adequately support the claim.

STRICT RULES:

1. Never invent claim IDs.
2. Never invent source IDs.
3. Search ranking is not verification.
4. Quantitative claims require strong
   corroboration.
5. Benchmark authors describing their own
   benchmark are not independent validation.
6. Marketing claims require corroboration.
7. A narrow product capability can have strong
   evidence from official first-party
   documentation.
8. Claims comparing multiple products generally
   need evidence covering those products.
9. supporting_source_ids must list all supplied
   sources that actually support the claim.
10. contradicting_source_ids must list sources
    that directly disagree.
11. Keep rationale concise.
12. Return one decision per supplied claim.
13. Return structured JSON only.
""".strip()


FIRST_PARTY_RULES = {
    "crewai": (
        "crewai.com",
        "github.com/crewAIInc/crewAI",
    ),
    "langgraph": (
        "langchain.com",
        "github.com/langchain-ai/langgraph",
    ),
}


HIGH_CORROBORATION_TERMS = (
    "benchmark",
    "latency",
    "throughput",
    "requests per second",
    "rps",
    "faster",
    "slower",
    "cheaper",
    "cost",
    "token overhead",
    "best",
    "better",
    "worse",
    "strongest",
    "recommended",
    "production-grade",
    "scientific",
    "under an hour",
)


SUBJECTIVE_EVALUATION_TERMS = (
    "best",
    "better",
    "worse",
    "strongest",
    "recommended",
    "recommend ",
    "ideal",
    "easiest",
)


class VerificationService:

    def __init__(
        self,
        llm: StructuredLLM,
    ) -> None:

        self.llm = llm

    @staticmethod
    def _unique(
        values: list[str],
    ) -> list[str]:

        result = []
        seen = set()

        for value in values:

            if value in seen:
                continue

            seen.add(value)

            result.append(
                value
            )

        return result

    @staticmethod
    def _domain_count(
        source_ids: list[str],
        source_lookup: dict[
            str,
            SearchResult,
        ],
    ) -> int:

        domains = set()

        for source_id in source_ids:

            source = source_lookup.get(
                source_id
            )

            if source is None:
                continue

            domains.add(
                source.domain.casefold()
            )

        return len(domains)

    @staticmethod
    def _requires_corroboration(
        claim: str,
    ) -> bool:

        normalized = (
            claim.casefold()
        )

        if re.search(
            r"\d",
            normalized,
        ):
            return True

        if (
            "langgraph" in normalized
            and "crewai" in normalized
        ):
            return True

        return any(
            term in normalized
            for term
            in HIGH_CORROBORATION_TERMS
        )

    @staticmethod
    def _has_strong_source(
        source_ids,
        source_lookup,
    ) -> bool:

        strong_categories = {
            "academic",
            "documentation",
            "repository",
            "government",
        }

        return any(
            (
                source_lookup.get(source_id)
                is not None
                and source_lookup[
                    source_id
                ].source_category
                in strong_categories
            )
            for source_id
            in source_ids
        )

    @staticmethod
    def _is_subjective_evaluation(
        claim: str,
    ) -> bool:

        normalized = claim.casefold()

        return any(
            term in normalized
            for term
            in SUBJECTIVE_EVALUATION_TERMS
        )

    @staticmethod
    def _is_first_party(
        claim: str,
        source: SearchResult,
    ) -> bool:

        if source.source_category not in {
            "documentation",
            "repository",
        }:
            return False

        normalized_claim = (
            claim.casefold()
        )

        normalized_url = (
            str(source.url)
            .casefold()
        )

        for product, markers in (
            FIRST_PARTY_RULES.items()
        ):

            if (
                product
                not in normalized_claim
            ):
                continue

            if any(
                marker.casefold()
                in normalized_url
                for marker
                in markers
            ):
                return True

        # Generic conservative fallback:
        # docs.product.com can verify a claim
        # explicitly mentioning "product".
        labels = (
            source.domain
            .casefold()
            .split(".")
        )

        if len(labels) >= 2:

            root = labels[-2].replace(
                "-",
                "",
            )

            compact_claim = (
                normalized_claim
                .replace("-", "")
                .replace("_", "")
            )

            if (
                len(root) >= 4
                and root in compact_claim
            ):
                return True

        return False

    def _single_source_can_verify(
        self,
        claim: str,
        source_ids: list[str],
        source_lookup: dict[
            str,
            SearchResult,
        ],
    ) -> bool:

        if (
            len(source_ids) != 1
        ):
            return False

        if self._requires_corroboration(
            claim
        ):
            return False

        source = source_lookup.get(
            source_ids[0]
        )

        if source is None:
            return False

        return self._is_first_party(
            claim,
            source,
        )

    @staticmethod
    def _unsupported(
        claim: ConsolidatedClaim,
        reason: str,
    ) -> VerifiedClaim:

        return VerifiedClaim(
            claim_id=claim.id,
            question_id=(
                claim.question_id
            ),
            claim=claim.claim,
            finding_ids=(
                claim.finding_ids
            ),
            status="UNSUPPORTED",
            confidence=0.0,
            supporting_source_ids=[],
            contradicting_source_ids=[],
            rationale=reason,
            caveats=[
                (
                    "Verification decision "
                    "was not sufficiently "
                    "grounded."
                )
            ],
        )

    def verify(
        self,
        plan: ResearchPlan,
        corpus: SearchCorpus,
        source_corpus: SourceContentCorpus,
        claims: ClaimCorpus,
    ) -> VerificationCorpus:

        source_lookup = {
            source.id: source
            for source
            in corpus.results
        }

        fetched_ids = {
            source.source_id
            for source
            in source_corpus.results
            if source.status == "fetched"
        }

        claims_by_question = {
            question.id: []
            for question
            in plan.questions
        }

        for claim in claims.claims:

            if (
                claim.question_id
                in claims_by_question
            ):
                claims_by_question[
                    claim.question_id
                ].append(
                    claim
                )

        results: list[
            VerifiedClaim
        ] = []

        for question in plan.questions:

            question_claims = (
                claims_by_question.get(
                    question.id,
                    [],
                )
            )[:4]

            if not question_claims:
                continue

            question_source_ids = (
                self._unique(
                    [
                        source_id
                        for claim
                        in question_claims
                        for source_id
                        in claim.source_ids
                        if source_id
                        in fetched_ids
                    ]
                )
            )

            source_payload = []

            for source_id in (
                question_source_ids
            ):

                source = (
                    source_lookup.get(
                        source_id
                    )
                )

                if source is None:
                    continue

                source_payload.append(
                    {
                        "id": source.id,
                        "title": (
                            source.title
                        ),
                        "url": str(
                            source.url
                        ),
                        "domain": (
                            source.domain
                        ),
                        "source_category": (
                            source
                            .source_category
                        ),
                        "authority_score": (
                            source
                            .authority_score
                        ),
                    }
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
                "sources": source_payload,
                "claims": [
                    {
                        "id": claim.id,
                        "claim": (
                            claim.claim
                        ),
                        "members": [
                            {
                                "finding_id": (
                                    member
                                    .finding_id
                                ),
                                "source_id": (
                                    member
                                    .source_id
                                ),
                                "claim": (
                                    member.claim
                                ),
                                "evidence_excerpt": (
                                    member
                                    .evidence_excerpt
                                ),
                                "evidence_type": (
                                    member
                                    .evidence_type
                                ),
                            }
                            for member
                            in claim.members
                        ],
                    }
                    for claim
                    in question_claims
                ],
            }

            try:

                draft = (
                    self.llm
                    .generate_structured(
                        system_prompt=(
                            VERIFICATION_SYSTEM_PROMPT
                        ),
                        user_prompt=(
                            "Verify these consolidated "
                            "claims for one research "
                            "question.\n\n"
                            + json.dumps(
                                payload,
                                ensure_ascii=False,
                                indent=2,
                            )
                        ),
                        schema=(
                            QuestionVerificationDraft
                        ),
                    )
                )

            except Exception:

                for claim in (
                    question_claims
                ):

                    results.append(
                        self._unsupported(
                            claim,
                            (
                                "Verification model "
                                "failed to return a "
                                "valid decision."
                            ),
                        )
                    )

                continue

            # Do not trust the LLM-generated
            # question_id as an authorization
            # boundary.
            #
            # This call is already scoped to one
            # question, and decisions below are
            # deterministically filtered against
            # the valid claim IDs for THIS batch.
            #
            # A wrong question_id is therefore
            # harmless metadata noise and must
            # not invalidate otherwise grounded
            # verification decisions.
            valid_claim_ids = {
                claim.id
                for claim
                in question_claims
            }

            decisions = {
                decision.claim_id: decision
                for decision
                in draft.decisions
                if decision.claim_id
                in valid_claim_ids
            }

            for claim in (
                question_claims
            ):

                # Claim-level traceability:
                # a verifier decision may only
                # cite evidence members that
                # actually belong to THIS
                # consolidated claim.
                claim_support_source_ids = {
                    member.source_id
                    for member in claim.members
                    if (
                        member.evidence_type
                        == "supporting"
                        and member.source_id
                        in fetched_ids
                    )
                }

                claim_conflict_source_ids = {
                    member.source_id
                    for member in claim.members
                    if (
                        member.evidence_type
                        == "contradicting"
                        and member.source_id
                        in fetched_ids
                    )
                }

                decision = decisions.get(
                    claim.id
                )

                if decision is None:

                    results.append(
                        self._unsupported(
                            claim,
                            (
                                "Verifier omitted "
                                "this claim."
                            ),
                        )
                    )

                    continue

                support = self._unique(
                    [
                        source_id
                        for source_id
                        in decision
                        .supporting_source_ids
                        if source_id
                        in claim_support_source_ids
                    ]
                )

                conflicts = self._unique(
                    [
                        source_id
                        for source_id
                        in decision
                        .contradicting_source_ids
                        if source_id
                        in claim_conflict_source_ids
                    ]
                )

                status: VerificationStatus = (
                    decision.status
                )

                confidence = (
                    decision.confidence
                )

                if (
                    status != "UNSUPPORTED"
                    and not support
                ):

                    # Preserve only genuinely
                    # grounded supporting members.
                    support = [
                        source_id
                        for source_id
                        in claim.source_ids
                        if source_id
                        in claim_support_source_ids
                    ]

                domain_count = (
                    self._domain_count(
                        support,
                        source_lookup,
                    )
                )

                requires_strong_corroboration = (
                    self._requires_corroboration(
                        claim.claim
                    )
                )

                has_strong_source = (
                    self._has_strong_source(
                        support,
                        source_lookup,
                    )
                )

                subjective_evaluation = (
                    self._is_subjective_evaluation(
                        claim.claim
                    )
                )

                if (
                    status == "VERIFIED"
                    and not subjective_evaluation
                ):

                    independently_supported = (
                        domain_count >= 2
                    )

                    official_single_source = (
                        self
                        ._single_source_can_verify(
                            claim.claim,
                            support,
                            source_lookup,
                        )
                    )

                    if not (
                        independently_supported
                        or official_single_source
                    ):

                        status = (
                            "PARTIALLY_VERIFIED"
                        )

                        confidence = min(
                            confidence,
                            0.75,
                        )

                    elif official_single_source:

                        confidence = min(
                            confidence,
                            0.92,
                        )

                # Recommendations and subjective
                # superlatives are contextual, not
                # objective facts. Even multiple
                # agreeing sources do not make
                # "best" universally verified.
                if (
                    status == "VERIFIED"
                    and subjective_evaluation
                ):
                    status = (
                        "PARTIALLY_VERIFIED"
                    )

                    confidence = min(
                        confidence,
                        0.79,
                    )

                # Web research should not express
                # absolute certainty.
                if status == "VERIFIED":
                    confidence = min(
                        confidence,
                        0.97,
                    )

                # Benchmark, latency, throughput,
                # cost and similar high-risk claims
                # must not become VERIFIED merely
                # because multiple general-web
                # pages repeat the same assertion.
                if (
                    status == "VERIFIED"
                    and requires_strong_corroboration
                    and not has_strong_source
                ):
                    status = (
                        "PARTIALLY_VERIFIED"
                    )

                    confidence = min(
                        confidence,
                        0.79,
                    )

                # Hard traceability invariant:
                # VERIFIED/PARTIAL claims must
                # always have grounded supporting
                # evidence.
                if (
                    status
                    in {
                        "VERIFIED",
                        "PARTIALLY_VERIFIED",
                    }
                    and not support
                ):
                    status = "UNSUPPORTED"

                    confidence = min(
                        confidence,
                        0.35,
                    )

                if (
                    status == "CONFLICTING"
                    and not conflicts
                ):

                    if support:

                        status = (
                            "PARTIALLY_VERIFIED"
                        )

                        confidence = min(
                            confidence,
                            0.70,
                        )

                    else:

                        status = (
                            "UNSUPPORTED"
                        )

                        confidence = min(
                            confidence,
                            0.35,
                        )

                if (
                    status
                    == "PARTIALLY_VERIFIED"
                ):

                    confidence = min(
                        confidence,
                        0.79,
                    )

                if (
                    status
                    == "UNSUPPORTED"
                ):

                    confidence = min(
                        confidence,
                        0.35,
                    )

                    support = []

                caveats = [
                    item.strip()
                    for item
                    in decision.caveats[:4]
                    if item.strip()
                ]

                if (
                    status
                    == "PARTIALLY_VERIFIED"
                    and domain_count < 2
                ):

                    caveat = (
                        "No independent "
                        "cross-domain "
                        "corroboration."
                    )

                    if caveat not in caveats:

                        caveats.append(
                            caveat
                        )

                if (
                    status
                    == "PARTIALLY_VERIFIED"
                    and subjective_evaluation
                ):

                    caveat = (
                        "Evaluative recommendation "
                        "depends on workload, "
                        "requirements, and criteria."
                    )

                    if caveat not in caveats:
                        caveats.append(
                            caveat
                        )

                results.append(
                    VerifiedClaim(
                        claim_id=claim.id,
                        question_id=(
                            claim.question_id
                        ),
                        claim=claim.claim,
                        finding_ids=(
                            claim.finding_ids
                        ),
                        status=status,
                        confidence=round(
                            confidence,
                            3,
                        ),
                        supporting_source_ids=(
                            support
                        ),
                        contradicting_source_ids=(
                            conflicts
                        ),
                        rationale=(
                            decision.rationale
                        ),
                        caveats=caveats,
                    )
                )

        return VerificationCorpus(
            total_claims=len(
                results
            ),
            verified_claims=sum(
                claim.status
                == "VERIFIED"
                for claim in results
            ),
            partially_verified_claims=sum(
                claim.status
                == "PARTIALLY_VERIFIED"
                for claim in results
            ),
            conflicting_claims=sum(
                claim.status
                == "CONFLICTING"
                for claim in results
            ),
            unsupported_claims=sum(
                claim.status
                == "UNSUPPORTED"
                for claim in results
            ),
            claims=results,
        )
