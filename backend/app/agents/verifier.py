from app.graph.state import (
    ResearchState,
)
from app.services.verification import (
    VerificationService,
)


def build_verifier_node(
    service: VerificationService,
):

    def verifier_node(
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

        source_corpus = state.get(
            "source_corpus"
        )

        claims = state.get(
            "claims"
        )

        if plan is None:
            return {
                "errors": [
                    "Verification failed: "
                    "missing plan"
                ]
            }

        if corpus is None:
            return {
                "errors": [
                    "Verification failed: "
                    "missing search corpus"
                ]
            }

        if source_corpus is None:
            return {
                "errors": [
                    "Verification failed: "
                    "missing fetched sources"
                ]
            }

        if claims is None:
            return {
                "errors": [
                    "Verification failed: "
                    "missing consolidated claims"
                ]
            }

        try:

            verification = (
                service.verify(
                    plan,
                    corpus,
                    source_corpus,
                    claims,
                )
            )

        except Exception as exc:

            return {
                "errors": [
                    "Verification failed: "
                    f"{exc}"
                ]
            }

        return {
            "verification": verification,
            "errors": [],
        }

    return verifier_node
