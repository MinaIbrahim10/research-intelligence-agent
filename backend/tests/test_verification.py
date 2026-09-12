from app.schemas.claims import (
    ClaimCorpus,
    ClaimEvidenceMember,
    ConsolidatedClaim,
)
from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.schemas.source import (
    FetchedSource,
    SourceContentCorpus,
)
from app.schemas.verification import (
    QuestionVerificationDraft,
    VerificationDecision,
)
from app.services.verification import (
    VerificationService,
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
                    "How does architecture differ?"
                ),
                purpose=(
                    "Compare architecture."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "What production capabilities "
                    "does CrewAI expose?"
                ),
                purpose=(
                    "Evaluate capabilities."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "What benchmark results exist?"
                ),
                purpose=(
                    "Evaluate benchmarks."
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
            "Frameworks change rapidly."
        ),
        success_criteria=[
            "Use direct evidence.",
            "Use reliable sources.",
        ],
    )


def make_corpus():

    return SearchCorpus(
        total_queries=3,
        unique_sources=4,
        results=[
            SearchResult(
                id="s1",
                title="Source A",
                url=(
                    "https://example-a.com/a"
                ),
                content="snippet",
                domain="example-a.com",
                source_category="general_web",
                provider_score=0.9,
                authority_score=0.55,
                final_score=0.70,
                question_ids=["q1"],
            ),
            SearchResult(
                id="s2",
                title="Source B",
                url=(
                    "https://example-b.org/b"
                ),
                content="snippet",
                domain="example-b.org",
                source_category="general_web",
                provider_score=0.9,
                authority_score=0.55,
                final_score=0.70,
                question_ids=["q1"],
            ),
            SearchResult(
                id="s3",
                title="CrewAI Docs",
                url=(
                    "https://docs.crewai.com/"
                    "enterprise"
                ),
                content="snippet",
                domain="docs.crewai.com",
                source_category="documentation",
                provider_score=0.9,
                authority_score=0.98,
                final_score=0.94,
                question_ids=["q2"],
            ),
            SearchResult(
                id="s4",
                title="Benchmark Blog",
                url=(
                    "https://benchmark.example/"
                    "results"
                ),
                content="snippet",
                domain="benchmark.example",
                source_category="general_web",
                provider_score=0.8,
                authority_score=0.55,
                final_score=0.66,
                question_ids=["q3"],
            ),
        ],
    )


def make_sources():

    results = []

    for source in make_corpus().results:

        content = (
            "Full fetched content "
            "for verification."
        )

        results.append(
            FetchedSource(
                source_id=source.id,
                title=source.title,
                url=source.url,
                final_url=source.url,
                question_ids=(
                    source.question_ids
                ),
                source_category=(
                    source.source_category
                ),
                final_score=(
                    source.final_score
                ),
                content=content,
                content_chars=len(
                    content
                ),
                content_type="text/html",
                status="fetched",
            )
        )

    return SourceContentCorpus(
        attempted_sources=4,
        fetched_sources=4,
        failed_sources=0,
        results=results,
    )


def member(
    finding_id,
    source_id,
    claim,
):

    return ClaimEvidenceMember(
        finding_id=finding_id,
        source_id=source_id,
        claim=claim,
        evidence_excerpt=claim,
        evidence_type="supporting",
    )


def make_claims():

    c1_claim = (
        "LangGraph uses explicit "
        "state graph control."
    )

    c2_claim = (
        "CrewAI provides deployment "
        "management through its "
        "Enterprise console."
    )

    c3_claim = (
        "LangGraph benchmark latency "
        "is 1.2 seconds."
    )

    return ClaimCorpus(
        total_claims=3,
        claims=[
            ConsolidatedClaim(
                id="c1",
                question_id="q1",
                claim=c1_claim,
                finding_ids=[
                    "e1",
                    "e2",
                ],
                source_ids=[
                    "s1",
                    "s2",
                ],
                members=[
                    member(
                        "e1",
                        "s1",
                        c1_claim,
                    ),
                    member(
                        "e2",
                        "s2",
                        c1_claim,
                    ),
                ],
            ),
            ConsolidatedClaim(
                id="c2",
                question_id="q2",
                claim=c2_claim,
                finding_ids=[
                    "e3",
                ],
                source_ids=[
                    "s3",
                ],
                members=[
                    member(
                        "e3",
                        "s3",
                        c2_claim,
                    )
                ],
            ),
            ConsolidatedClaim(
                id="c3",
                question_id="q3",
                claim=c3_claim,
                finding_ids=[
                    "e4",
                ],
                source_ids=[
                    "s4",
                ],
                members=[
                    member(
                        "e4",
                        "s4",
                        c3_claim,
                    )
                ],
            ),
        ],
    )


class FakeVerificationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        if '"id": "q1"' in user_prompt:

            return QuestionVerificationDraft(
                question_id="q1",
                decisions=[
                    VerificationDecision(
                        claim_id="c1",
                        status="VERIFIED",
                        confidence=0.95,
                        supporting_source_ids=[
                            "s1",
                            "s2",
                        ],
                        contradicting_source_ids=[],
                        rationale=(
                            "Independent sources "
                            "corroborate the claim."
                        ),
                        caveats=[],
                    )
                ],
            )

        if '"id": "q2"' in user_prompt:

            return QuestionVerificationDraft(
                question_id="q2",
                decisions=[
                    VerificationDecision(
                        claim_id="c2",
                        status="VERIFIED",
                        confidence=0.96,
                        supporting_source_ids=[
                            "s3",
                        ],
                        contradicting_source_ids=[],
                        rationale=(
                            "Official CrewAI "
                            "documentation supports it."
                        ),
                        caveats=[],
                    )
                ],
            )

        return QuestionVerificationDraft(
            question_id="q3",
            decisions=[
                VerificationDecision(
                    claim_id="c3",
                    status="VERIFIED",
                    confidence=0.95,
                    supporting_source_ids=[
                        "s4",
                    ],
                    contradicting_source_ids=[],
                    rationale=(
                        "Single benchmark source."
                    ),
                    caveats=[],
                )
            ],
        )


def test_independent_sources_can_verify():

    result = VerificationService(
        FakeVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        make_claims(),
    )

    claim = next(
        item
        for item in result.claims
        if item.claim_id == "c1"
    )

    assert claim.status == "VERIFIED"


def test_narrow_first_party_capability_can_verify():

    result = VerificationService(
        FakeVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        make_claims(),
    )

    claim = next(
        item
        for item in result.claims
        if item.claim_id == "c2"
    )

    assert claim.status == "VERIFIED"

    assert claim.confidence <= 0.92


def test_single_source_quantitative_claim_is_downgraded():

    result = VerificationService(
        FakeVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        make_claims(),
    )

    claim = next(
        item
        for item in result.claims
        if item.claim_id == "c3"
    )

    assert (
        claim.status
        == "PARTIALLY_VERIFIED"
    )

    assert claim.confidence <= 0.75


class SubjectiveVerificationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionVerificationDraft(
            question_id="q1",
            decisions=[
                VerificationDecision(
                    claim_id="c99",
                    status="VERIFIED",
                    confidence=1.0,
                    supporting_source_ids=[
                        "s1",
                        "s2",
                    ],
                    contradicting_source_ids=[],
                    rationale=(
                        "Two sources recommend it."
                    ),
                    caveats=[],
                )
            ],
        )


def test_subjective_recommendation_cannot_be_fully_verified():

    claim_text = (
        "LangGraph is best for "
        "complex workflows."
    )

    claims = ClaimCorpus(
        total_claims=1,
        claims=[
            ConsolidatedClaim(
                id="c99",
                question_id="q1",
                claim=claim_text,
                finding_ids=[
                    "e99a",
                    "e99b",
                ],
                source_ids=[
                    "s1",
                    "s2",
                ],
                members=[
                    member(
                        "e99a",
                        "s1",
                        claim_text,
                    ),
                    member(
                        "e99b",
                        "s2",
                        claim_text,
                    ),
                ],
            )
        ],
    )

    result = VerificationService(
        SubjectiveVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        claims,
    )

    claim = result.claims[0]

    assert (
        claim.status
        == "PARTIALLY_VERIFIED"
    )

    assert claim.confidence <= 0.79


def test_verified_confidence_is_capped():

    result = VerificationService(
        FakeVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        make_claims(),
    )

    verified = [
        claim
        for claim in result.claims
        if claim.status == "VERIFIED"
    ]

    assert verified

    assert all(
        claim.confidence <= 0.97
        for claim in verified
    )


class SourceLeakageVerificationLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionVerificationDraft(
            question_id="q1",
            decisions=[
                VerificationDecision(
                    claim_id="c100",
                    status="VERIFIED",
                    confidence=0.99,
                    supporting_source_ids=[
                        "s1",
                        "s2",
                    ],
                    contradicting_source_ids=[],
                    rationale=(
                        "Claims two sources "
                        "support it."
                    ),
                    caveats=[],
                ),
                VerificationDecision(
                    claim_id="c101",
                    status="PARTIALLY_VERIFIED",
                    confidence=0.70,
                    supporting_source_ids=[
                        "s2",
                    ],
                    contradicting_source_ids=[],
                    rationale="Direct support.",
                    caveats=[],
                ),
            ],
        )


def test_verifier_cannot_borrow_source_from_sibling_claim():

    claim_a = (
        "LangGraph uses explicit "
        "graph state."
    )

    claim_b = (
        "CrewAI uses role-based teams."
    )

    claims = ClaimCorpus(
        total_claims=2,
        claims=[
            ConsolidatedClaim(
                id="c100",
                question_id="q1",
                claim=claim_a,
                finding_ids=["e100"],
                source_ids=["s1"],
                members=[
                    member(
                        "e100",
                        "s1",
                        claim_a,
                    )
                ],
            ),
            ConsolidatedClaim(
                id="c101",
                question_id="q1",
                claim=claim_b,
                finding_ids=["e101"],
                source_ids=["s2"],
                members=[
                    member(
                        "e101",
                        "s2",
                        claim_b,
                    )
                ],
            ),
        ],
    )

    result = VerificationService(
        SourceLeakageVerificationLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        claims,
    )

    first = next(
        claim
        for claim in result.claims
        if claim.claim_id == "c100"
    )

    assert first.supporting_source_ids == [
        "s1"
    ]

    assert (
        first.status
        == "PARTIALLY_VERIFIED"
    )

    assert first.confidence <= 0.75


class WrongQuestionIdButValidClaimsLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionVerificationDraft(
            # Intentionally wrong metadata.
            question_id="q999",
            decisions=[
                VerificationDecision(
                    claim_id="c100",
                    status="VERIFIED",
                    confidence=0.95,
                    supporting_source_ids=[
                        "s1",
                    ],
                    contradicting_source_ids=[],
                    rationale=(
                        "The supplied evidence "
                        "directly supports it."
                    ),
                    caveats=[],
                )
            ],
        )


def test_wrong_question_id_does_not_discard_valid_claim_decision():

    claim_text = (
        "LangGraph uses explicit "
        "graph state."
    )

    claims = ClaimCorpus(
        total_claims=1,
        claims=[
            ConsolidatedClaim(
                id="c100",
                question_id="q1",
                claim=claim_text,
                finding_ids=[
                    "e100",
                ],
                source_ids=[
                    "s1",
                ],
                members=[
                    member(
                        "e100",
                        "s1",
                        claim_text,
                    )
                ],
            )
        ],
    )

    result = VerificationService(
        WrongQuestionIdButValidClaimsLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        claims,
    )

    assert result.total_claims == 1

    claim = result.claims[0]

    # It must be evaluated from its valid claim
    # ID instead of being discarded because of
    # noisy LLM question metadata.
    assert (
        claim.status
        != "UNSUPPORTED"
    )

    assert claim.supporting_source_ids == [
        "s1"
    ]


class WrongQuestionAndHallucinatedClaimLLM:

    def generate_structured(
        self,
        *,
        system_prompt,
        user_prompt,
        schema,
    ):

        return QuestionVerificationDraft(
            question_id="q999",
            decisions=[
                VerificationDecision(
                    claim_id="c999",
                    status="VERIFIED",
                    confidence=0.99,
                    supporting_source_ids=[
                        "s1",
                    ],
                    contradicting_source_ids=[],
                    rationale="Invented decision.",
                    caveats=[],
                )
            ],
        )


def test_wrong_question_cannot_inject_foreign_claim():

    claim_text = (
        "LangGraph uses explicit "
        "graph state."
    )

    claims = ClaimCorpus(
        total_claims=1,
        claims=[
            ConsolidatedClaim(
                id="c100",
                question_id="q1",
                claim=claim_text,
                finding_ids=[
                    "e100",
                ],
                source_ids=[
                    "s1",
                ],
                members=[
                    member(
                        "e100",
                        "s1",
                        claim_text,
                    )
                ],
            )
        ],
    )

    result = VerificationService(
        WrongQuestionAndHallucinatedClaimLLM()
    ).verify(
        make_plan(),
        make_corpus(),
        make_sources(),
        claims,
    )

    claim = result.claims[0]

    # Hallucinated c999 is filtered out.
    # Since the real c100 was omitted,
    # fail closed.
    assert (
        claim.status
        == "UNSUPPORTED"
    )
