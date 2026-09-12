from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.services.searching import (
    SearchService,
    canonicalize_url,
    classify_source,
)
from app.tools.searxng_search import (
    RawSearchResult,
)


class FakeSearchClient:

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ):

        if "LangGraph" in query:

            return [
                RawSearchResult(
                    title="LangGraph docs",
                    url=(
                        "https://docs.langchain.com/"
                        "langgraph/?utm_source=test"
                    ),
                    content=(
                        "Official documentation"
                    ),
                    score=0.95,
                    engine="brave",
                ),
                RawSearchResult(
                    title="Shared source",
                    url=(
                        "https://example.com/"
                        "article#section"
                    ),
                    content="First snippet",
                    score=0.70,
                    engine="brave",
                ),
            ]

        return [
            RawSearchResult(
                title=(
                    "Shared source updated"
                ),
                url=(
                    "https://example.com/"
                    "article/"
                ),
                content="Better snippet",
                score=0.90,
                engine="brave",
            )
        ]


def make_plan() -> ResearchPlan:

    return ResearchPlan(
        objective=(
            "Compare two agent frameworks "
            "for production use."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "What production features "
                    "does LangGraph provide?"
                ),
                purpose=(
                    "Assess LangGraph "
                    "production readiness."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "What production features "
                    "does CrewAI provide?"
                ),
                purpose=(
                    "Assess CrewAI "
                    "production readiness."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "How do their deployment "
                    "models differ in practice?"
                ),
                purpose=(
                    "Compare deployment "
                    "tradeoffs."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "official docs",
            "repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Framework capabilities "
            "change frequently."
        ),
        success_criteria=[
            "Use current official evidence",
            "Compare both frameworks",
        ],
    )


def test_canonicalize_url_removes_tracking_and_fragment():

    value = canonicalize_url(
        "https://Example.com/docs/"
        "?utm_source=x&id=4#intro"
    )

    assert value == (
        "https://example.com/docs?id=4"
    )


def test_classify_source_recognizes_docs_and_repositories():

    assert (
        classify_source(
            "https://docs.example.com/guide"
        )
        == "documentation"
    )

    assert (
        classify_source(
            "https://github.com/org/repo"
        )
        == "repository"
    )


def test_search_service_deduplicates_and_merges_question_ids():

    corpus = SearchService(
        FakeSearchClient(),
        max_results_per_query=5,
    ).search_plan(
        make_plan()
    )

    assert corpus.total_queries == 3
    assert corpus.unique_sources == 2

    shared = next(
        item
        for item in corpus.results
        if item.domain == "example.com"
    )

    assert shared.provider_score == 0.90
    assert shared.content == "Better snippet"

    assert shared.question_ids == [
        "q1",
        "q2",
        "q3",
    ]

    docs = next(
        item
        for item in corpus.results
        if item.domain
        == "docs.langchain.com"
    )

    assert (
        docs.source_category
        == "documentation"
    )
