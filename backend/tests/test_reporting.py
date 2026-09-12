from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.schemas.verification import (
    VerificationCorpus,
    VerifiedClaim,
)
from app.services.reporting import (
    ReportService,
)


def make_plan():

    return ResearchPlan(
        objective="Compare frameworks.",
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How do architectures differ?"
                ),
                purpose="Architecture.",
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "What benchmarks exist?"
                ),
                purpose="Performance.",
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "What gaps remain?"
                ),
                purpose="Coverage.",
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "documentation",
            "repositories",
        ],
        freshness_required=True,
        freshness_reason="Changes quickly.",
        success_criteria=[
            "Use evidence.",
            "Cite sources.",
        ],
    )


def make_corpus():

    return SearchCorpus(
        total_queries=2,
        unique_sources=2,
        results=[
            SearchResult(
                id="s1",
                title="Source One",
                url="https://a.example/x",
                content="snippet",
                domain="a.example",
                source_category="documentation",
                provider_score=0.9,
                authority_score=0.9,
                final_score=0.9,
                question_ids=["q1"],
            ),
            SearchResult(
                id="s2",
                title="Source Two",
                url="https://b.example/y",
                content="snippet",
                domain="b.example",
                source_category="general_web",
                provider_score=0.8,
                authority_score=0.6,
                final_score=0.7,
                question_ids=["q2"],
            ),
        ],
    )


def make_verification():

    return VerificationCorpus(
        total_claims=2,
        verified_claims=1,
        partially_verified_claims=1,
        conflicting_claims=0,
        unsupported_claims=0,
        claims=[
            VerifiedClaim(
                claim_id="c1",
                question_id="q1",
                claim=(
                    "Framework A uses explicit "
                    "graph state."
                ),
                finding_ids=["e1"],
                status="VERIFIED",
                confidence=0.95,
                supporting_source_ids=["s1"],
                contradicting_source_ids=[],
                rationale="Direct support.",
                caveats=[],
            ),
            VerifiedClaim(
                claim_id="c2",
                question_id="q2",
                claim=(
                    "Framework A has lower "
                    "latency."
                ),
                finding_ids=["e2"],
                status=(
                    "PARTIALLY_VERIFIED"
                ),
                confidence=0.75,
                supporting_source_ids=["s2"],
                contradicting_source_ids=[],
                rationale=(
                    "Single benchmark."
                ),
                caveats=[
                    (
                        "No independent "
                        "corroboration."
                    )
                ],
            ),
        ],
    )


def test_partial_claim_is_qualified():

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=(
            make_verification()
        ),
    )

    section = next(
        item
        for item in report.sections
        if item.question_id == "q2"
    )

    statement = (
        section.claims[0]
        .statement
    )

    assert statement.startswith(
        "Available evidence supports "
        "this claim, but it is not "
        "independently established:"
    )


def test_report_uses_only_referenced_sources():

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=(
            make_verification()
        ),
    )

    assert {
        source.id
        for source in report.sources
    } == {
        "s1",
        "s2",
    }


def test_missing_question_evidence_becomes_gap():

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=(
            make_verification()
        ),
    )

    q3 = next(
        item
        for item in report.sections
        if item.question_id == "q3"
    )

    assert q3.confidence == 0.0

    assert q3.gaps


def test_markdown_contains_traceable_citations():

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=(
            make_verification()
        ),
    )

    assert "[s1]" in report.markdown
    assert "[s2]" in report.markdown

    assert "## Sources" in report.markdown


def test_report_does_not_upgrade_partial_status():

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=(
            make_verification()
        ),
    )

    q2 = next(
        item
        for item in report.sections
        if item.question_id == "q2"
    )

    assert (
        q2.claims[0].status
        == "PARTIALLY_VERIFIED"
    )


def make_comparison_plan():

    return ResearchPlan(
        objective=(
            "Compare LangGraph and CrewAI "
            "for production deployment."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How do both LangGraph "
                    "and CrewAI handle "
                    "production deployment?"
                ),
                purpose=(
                    "Compare production support."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How does each framework "
                    "handle reliability?"
                ),
                purpose=(
                    "Compare reliability."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "What evidence exists?"
                ),
                purpose=(
                    "Assess evidence."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "documentation",
            "repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Frameworks change."
        ),
        success_criteria=[
            "Cover LangGraph.",
            "Cover CrewAI.",
        ],
    )


def make_single_sided_verification():

    return VerificationCorpus(
        total_claims=1,
        verified_claims=1,
        partially_verified_claims=0,
        conflicting_claims=0,
        unsupported_claims=0,
        claims=[
            VerifiedClaim(
                claim_id="c10",
                question_id="q1",
                claim=(
                    "CrewAI provides "
                    "production deployment "
                    "controls."
                ),
                finding_ids=["e10"],
                status="VERIFIED",
                confidence=0.92,
                supporting_source_ids=[
                    "s1"
                ],
                contradicting_source_ids=[],
                rationale=(
                    "Official documentation."
                ),
                caveats=[],
            )
        ],
    )


def test_comparison_coverage_penalizes_single_sided_answer():

    report = ReportService().build(
        query=(
            "Compare LangGraph and CrewAI "
            "for production deployment"
        ),
        plan=make_comparison_plan(),
        corpus=make_corpus(),
        verification=(
            make_single_sided_verification()
        ),
    )

    q1 = next(
        section
        for section in report.sections
        if section.question_id == "q1"
    )

    assert {
        entity.casefold()
        for entity
        in q1.required_entities
    } == {
        "langgraph",
        "crewai",
    }

    assert [
        entity.casefold()
        for entity
        in q1.covered_entities
    ] == [
        "crewai"
    ]

    assert q1.coverage_ratio == 0.5

    assert q1.evidence_confidence == 0.92

    assert q1.confidence == 0.46

    assert any(
        "LangGraph" in gap
        for gap in q1.gaps
    )


def test_each_framework_inherits_objective_entities():

    report = ReportService().build(
        query=(
            "Compare LangGraph and CrewAI"
        ),
        plan=make_comparison_plan(),
        corpus=make_corpus(),
        verification=(
            make_single_sided_verification()
        ),
    )

    q2 = next(
        section
        for section in report.sections
        if section.question_id == "q2"
    )

    assert {
        entity.casefold()
        for entity
        in q2.required_entities
    } == {
        "langgraph",
        "crewai",
    }


def test_overall_confidence_uses_question_coverage():

    report = ReportService().build(
        query=(
            "Compare LangGraph and CrewAI"
        ),
        plan=make_comparison_plan(),
        corpus=make_corpus(),
        verification=(
            make_single_sided_verification()
        ),
    )

    # q1 = 0.46
    # q2 = 0.00 because no claims
    # q3 = 0.00 because no claims
    assert report.overall_confidence < 0.20


def test_unsupported_claim_is_not_displayed_as_finding():

    verification = VerificationCorpus(
        total_claims=1,
        verified_claims=0,
        partially_verified_claims=0,
        conflicting_claims=0,
        unsupported_claims=1,
        claims=[
            VerifiedClaim(
                claim_id="c999",
                question_id="q1",
                claim=(
                    "An unrelated unsupported "
                    "candidate claim."
                ),
                finding_ids=["e999"],
                status="UNSUPPORTED",
                confidence=0.35,
                supporting_source_ids=[],
                contradicting_source_ids=[],
                rationale=(
                    "Evidence does not support it."
                ),
                caveats=[],
            )
        ],
    )

    report = ReportService().build(
        query="Compare frameworks",
        plan=make_plan(),
        corpus=make_corpus(),
        verification=verification,
    )

    q1 = next(
        section
        for section in report.sections
        if section.question_id == "q1"
    )

    assert q1.claims == []

    assert any(
        "lack adequate support" in gap
        for gap in q1.gaps
    )
