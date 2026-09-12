import pytest

from app.agents.planner import build_planner_node
from app.schemas.planner import ResearchPlan
from app.services.planning import PlannerService
from tests.fakes import FakeStructuredLLM


def test_planner_service_returns_validated_research_plan():
    llm = FakeStructuredLLM()
    service = PlannerService(llm)

    plan = service.create_plan("Compare LangGraph and CrewAI for production agent systems")

    assert isinstance(plan, ResearchPlan)
    assert len(plan.questions) >= 3
    assert plan.freshness_required is True
    assert llm.calls[0]["schema"] is ResearchPlan
    assert "Do not answer" in llm.calls[0]["system_prompt"]


def test_planner_normalizes_whitespace_before_calling_llm():
    llm = FakeStructuredLLM()
    service = PlannerService(llm)

    service.create_plan("  Compare   two   current AI frameworks   ")

    assert "Compare two current AI frameworks" in llm.calls[0]["user_prompt"]


def test_planner_rejects_too_short_query():
    service = PlannerService(FakeStructuredLLM())

    with pytest.raises(ValueError, match="too short"):
        service.create_plan("AI?")


def test_planner_node_converts_provider_failure_to_graph_error():
    service = PlannerService(FakeStructuredLLM(error=RuntimeError("provider offline")))
    node = build_planner_node(service)

    result = node({"query": "Research a sufficiently long technical question", "errors": []})

    assert "plan" not in result
    assert result["errors"] == ["Planner failed: provider offline"]
