import hashlib

import pytest

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_planner_service,
    get_search_service,
)

from app.main import app

from app.services.planning import (
    PlannerService,
)

from app.services.searching import (
    SearchService,
)

from app.tools.searxng_search import (
    RawSearchResult,
)

from tests.fakes import FakeStructuredLLM


client = TestClient(app)


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
                title="Official-like evidence",
                url=(
                    "https://example.com/"
                    f"{source_id}"
                ),
                content="Evidence snippet",
                score=0.88,
                engine="brave",
            )
        ]


def test_health_endpoint():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "milestone": "search-v1",
    }


def test_plan_request_validation_rejects_short_query():

    response = client.post(
        "/api/v1/research/plan",
        json={
            "query": "short"
        },
    )

    assert response.status_code == 422


def test_plan_endpoint_when_langgraph_is_available():

    pytest.importorskip(
        "langgraph"
    )

    app.dependency_overrides[
        get_planner_service
    ] = lambda: PlannerService(
        FakeStructuredLLM()
    )

    try:

        response = client.post(
            "/api/v1/research/plan",
            json={
                "query": (
                    "Compare LangGraph "
                    "and CrewAI for "
                    "production agent systems"
                )
            },
        )

    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert (
        body["plan"]["freshness_required"]
        is True
    )

    assert (
        len(body["plan"]["questions"])
        == 3
    )


def test_search_endpoint_runs_planner_and_search():

    pytest.importorskip(
        "langgraph"
    )

    app.dependency_overrides[
        get_planner_service
    ] = lambda: PlannerService(
        FakeStructuredLLM()
    )

    app.dependency_overrides[
        get_search_service
    ] = lambda: SearchService(
        FakeSearchClient()
    )

    try:

        response = client.post(
            "/api/v1/research/search",
            json={
                "query": (
                    "Compare LangGraph "
                    "and CrewAI for "
                    "production agent systems"
                )
            },
        )

    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["query"].startswith(
        "Compare LangGraph"
    )

    assert (
        len(body["plan"]["questions"])
        == 3
    )

    assert (
        body["corpus"]["total_queries"]
        == 3
    )

    assert (
        body["corpus"]["unique_sources"]
        == 3
    )
