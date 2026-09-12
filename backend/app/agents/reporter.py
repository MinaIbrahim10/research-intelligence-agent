from app.graph.state import (
    ResearchState,
)
from app.services.reporting import (
    ReportService,
)


def build_reporter_node(
    service: ReportService,
):

    def reporter_node(
        state: ResearchState,
    ) -> dict:

        existing_errors = state.get(
            "errors",
            [],
        )

        if existing_errors:
            return {}

        query = state.get(
            "query"
        )

        plan = state.get(
            "plan"
        )

        corpus = state.get(
            "corpus"
        )

        verification = state.get(
            "verification"
        )

        if not query:
            return {
                "errors": [
                    "Report failed: "
                    "missing query"
                ]
            }

        if plan is None:
            return {
                "errors": [
                    "Report failed: "
                    "missing plan"
                ]
            }

        if corpus is None:
            return {
                "errors": [
                    "Report failed: "
                    "missing search corpus"
                ]
            }

        if verification is None:
            return {
                "errors": [
                    "Report failed: "
                    "missing verification"
                ]
            }

        try:

            report = service.build(
                query=query,
                plan=plan,
                corpus=corpus,
                verification=(
                    verification
                ),
            )

        except Exception as exc:

            return {
                "errors": [
                    "Report failed: "
                    f"{exc}"
                ]
            }

        return {
            "report": report,
            "errors": [],
        }

    return reporter_node
