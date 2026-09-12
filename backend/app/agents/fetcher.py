from app.graph.state import (
    ResearchState,
)
from app.services.fetching import (
    SourceFetchService,
)


def build_fetcher_node(
    service: SourceFetchService,
):

    def fetcher_node(
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

        corpus = state.get(
            "corpus"
        )

        if plan is None:
            return {
                "errors": [
                    "Source fetching failed: "
                    "missing research plan"
                ]
            }

        if corpus is None:
            return {
                "errors": [
                    "Source fetching failed: "
                    "missing search corpus"
                ]
            }

        try:
            source_corpus = (
                service.fetch_sources(
                    plan,
                    corpus,
                )
            )

        except Exception as exc:
            return {
                "errors": [
                    "Source fetching failed: "
                    f"{exc}"
                ]
            }

        return {
            "source_corpus": (
                source_corpus
            ),
            "errors": [],
        }

    return fetcher_node
