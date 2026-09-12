from app.graph.state import ResearchState
from app.services.planning import PlannerService


def build_planner_node(service: PlannerService):
    def planner_node(state: ResearchState) -> dict:
        query = state.get("query", "").strip()
        if not query:
            return {"errors": ["Missing research query"]}

        try:
            plan = service.create_plan(query)
        except Exception as exc:  # Boundary: provider + validation failures become graph state.
            return {"errors": [f"Planner failed: {exc}"]}

        return {"plan": plan, "errors": []}

    return planner_node
