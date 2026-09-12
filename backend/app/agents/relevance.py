from app.graph.state import (
    ResearchState,
)
from app.services.relevance import (
    EvidenceRelevanceService,
)


def build_relevance_node(
    service: EvidenceRelevanceService,
):

    def relevance_node(
        state: ResearchState,
    ) -> dict:

        existing_errors = state.get(
            "errors",
            [],
        )

        if existing_errors:
            return {}

        plan = state.get(
            "plan"
        )

        raw_evidence = state.get(
            "raw_evidence"
        )

        if plan is None:
            return {
                "errors": [
                    "Evidence relevance failed: "
                    "missing research plan"
                ]
            }

        if raw_evidence is None:
            return {
                "errors": [
                    "Evidence relevance failed: "
                    "missing raw evidence"
                ]
            }

        try:

            evidence = service.filter(
                plan,
                raw_evidence,
            )

        except Exception as exc:

            return {
                "errors": [
                    "Evidence relevance failed: "
                    f"{exc}"
                ]
            }

        return {
            "evidence": evidence,
            "errors": [],
        }

    return relevance_node
