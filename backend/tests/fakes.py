from app.schemas.planner import ResearchPlan, ResearchQuestion


class FakeStructuredLLM:
    def __init__(self, *, plan: ResearchPlan | None = None, error: Exception | None = None) -> None:
        self.plan = plan or sample_plan()
        self.error = error
        self.calls: list[dict] = []

    def generate_structured(self, *, system_prompt, user_prompt, schema):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "schema": schema,
            }
        )
        if self.error:
            raise self.error
        return self.plan


def sample_plan() -> ResearchPlan:
    return ResearchPlan(
        objective="Evaluate two agent frameworks for production use using current, primary evidence.",
        questions=[
            ResearchQuestion(
                id="q1",
                question="What architecture and execution model does each framework use?",
                purpose="Establish the technical baseline for comparison.",
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question="What production reliability and persistence features are documented?",
                purpose="Assess suitability for long-running production workflows.",
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question="What observability and human oversight capabilities are supported?",
                purpose="Assess operability and governance in production.",
                priority="medium",
            ),
        ],
        suggested_source_types=["official documentation", "official GitHub repositories"],
        freshness_required=True,
        freshness_reason="Framework capabilities and APIs change frequently.",
        success_criteria=[
            "Every material comparison is supported by primary evidence.",
            "Known limitations and conflicting evidence are recorded.",
        ],
    )
