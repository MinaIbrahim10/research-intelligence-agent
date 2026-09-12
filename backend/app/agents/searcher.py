from app.graph.state import ResearchState
from app.services.searching import SearchService


def build_search_node(service: SearchService):
    def search_node(state: ResearchState) -> dict:
        existing_errors = state.get("errors", [])

        if existing_errors:
            return {}

        plan = state.get("plan")

        if plan is None:
            return {
                "errors": [
                    "Search failed: missing research plan"
                ]
            }

        try:
            corpus = service.search_plan(plan)

        except Exception as exc:
            return {
                "errors": [
                    f"Search failed: {exc}"
                ]
            }

        return {
            "corpus": corpus,
            "errors": [],
        }

    return search_node
