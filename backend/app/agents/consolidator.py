from app.graph.state import (
    ResearchState,
)
from app.services.consolidation import (
    ClaimConsolidationService,
)


def build_consolidator_node(
    service: ClaimConsolidationService,
):

    def consolidator_node(
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

        evidence = state.get(
            "evidence"
        )

        if plan is None:
            return {
                "errors": [
                    "Claim consolidation failed: "
                    "missing research plan"
                ]
            }

        if evidence is None:
            return {
                "errors": [
                    "Claim consolidation failed: "
                    "missing evidence"
                ]
            }

        try:

            claims = (
                service.consolidate(
                    plan,
                    evidence,
                )
            )

        except Exception as exc:

            return {
                "errors": [
                    "Claim consolidation failed: "
                    f"{exc}"
                ]
            }

        return {
            "claims": claims,
            "errors": [],
        }

    return consolidator_node
