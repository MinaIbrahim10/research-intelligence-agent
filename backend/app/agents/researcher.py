from app.graph.state import (
    ResearchState,
)
from app.services.researching import (
    ResearchService,
)


def build_researcher_node(
    service: ResearchService,
):

    def researcher_node(
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

        source_corpus = state.get(
            "source_corpus"
        )

        if plan is None:
            return {
                "errors": [
                    "Research failed: "
                    "missing research plan"
                ]
            }

        if source_corpus is None:
            return {
                "errors": [
                    "Research failed: "
                    "missing fetched sources"
                ]
            }

        try:

            evidence = (
                service.extract_evidence(
                    plan,
                    source_corpus,
                )
            )

        except Exception as exc:

            return {
                "errors": [
                    f"Research failed: {exc}"
                ]
            }

        return {
            "raw_evidence": evidence,
            "errors": [],
        }

    return researcher_node
