import hashlib

import pytest

pytest.importorskip("langgraph")

from app.graph.workflow import (
    build_research_graph,
)
from app.services.planning import (
    PlannerService,
)
from app.services.searching import (
    SearchService,
)
from app.tools.searxng_search import (
    RawSearchResult,
)
from tests.fakes import (
    FakeStructuredLLM,
)


class FakeSearchClient:

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ):

        source_id = hashlib.sha256(
            query.encode()
        ).hexdigest()[:12]

        return [
            RawSearchResult(
                title=(
                    f"Evidence for {query}"
                ),
                url=(
                    "https://example.com/"
                    f"{source_id}"
                ),
                content="Evidence snippet",
                score=0.91,
                engine="brave",
            )
        ]


def test_research_graph_runs_planner_then_search():

    graph = build_research_graph(
        PlannerService(
            FakeStructuredLLM()
        ),
        SearchService(
            FakeSearchClient()
        ),
    )

    result = graph.invoke(
        {
            "query": (
                "Compare LangGraph and CrewAI "
                "for reliable production systems"
            ),
            "errors": [],
        }
    )

    assert result["plan"].objective

    assert (
        result["corpus"].total_queries
        == 3
    )

    assert (
        result["corpus"].unique_sources
        == 3
    )

    assert result["errors"] == []
