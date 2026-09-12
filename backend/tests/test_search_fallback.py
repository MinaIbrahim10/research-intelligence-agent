from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.services.searching import (
    SearchService,
    build_search_query_variants,
)
from app.tools.searxng_search import (
    RawSearchResult,
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
                    "How do they manage state?"
                ),
                purpose=(
                    "Compare state management."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How do they recover "
                    "from failures?"
                ),
                purpose=(
                    "Compare reliability."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "How complex are they "
                    "to implement?"
                ),
                purpose=(
                    "Compare developer "
                    "experience."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "Technical Documentation",
            "GitHub Repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Frameworks evolve quickly."
        ),
        success_criteria=[
            "Compare both frameworks.",
            "Use direct evidence.",
        ],
    )


class FallbackSearchClient:

    def __init__(self):
        self.calls = []

    def search(
        self,
        query,
        *,
        max_results=5,
    ):

        self.calls.append(query)

        # Pretend the two high-context
        # searches return nothing.
        if len(self.calls) < 3:
            return []

        return [
            RawSearchResult(
                title=(
                    "LangGraph state docs"
                ),
                url=(
                    "https://docs.example.com/"
                    "langgraph-state"
                ),
                content=(
                    "LangGraph state "
                    "documentation."
                ),
                score=0.9,
                engine="fake",
            )
        ]


def test_query_variants_get_broader():

    plan = make_plan()

    variants = (
        build_search_query_variants(
            plan,
            plan.questions[0],
        )
    )

    assert len(variants) == 3

    assert (
        "LangGraph"
        in variants[0]
    )

    assert (
        variants[-1]
        == "How do they manage state?"
    )


def test_search_falls_back_when_specific_queries_empty():

    client = (
        FallbackSearchClient()
    )

    service = SearchService(
        client,
        max_results_per_query=1,
    )

    # Test one question directly so call
    # ordering stays deterministic.
    results = service._search_question(
        make_plan(),
        make_plan().questions[0],
    )

    assert len(results) == 1

    assert (
        results[0].title
        == "LangGraph state docs"
    )

    assert len(client.calls) == 3
