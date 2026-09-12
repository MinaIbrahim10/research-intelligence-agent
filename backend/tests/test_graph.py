import pytest

langgraph = pytest.importorskip("langgraph")

from app.graph.workflow import build_planner_graph
from app.services.planning import PlannerService
from tests.fakes import FakeStructuredLLM


def test_planner_graph_runs_start_to_end():
    graph = build_planner_graph(PlannerService(FakeStructuredLLM()))
    result = graph.invoke({
        "query": "Compare two agent frameworks for reliable production systems",
        "errors": [],
    })

    assert result["plan"].objective
    assert result["errors"] == []
