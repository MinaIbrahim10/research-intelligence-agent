from app.providers.base import StructuredLLM
from app.schemas.planner import ResearchPlan


PLANNER_SYSTEM_PROMPT = """You are the Planner Agent in an evidence-first research system.
Your job is to turn one user research request into a focused research plan.

Rules:
- Do not answer the user's research question.
- Do not invent findings, sources, URLs, statistics, or conclusions.
- Break the request into 3 to 8 non-overlapping research questions.
- Prefer primary/official sources when they can answer the question.
- Mark freshness_required=true when the answer may materially change over time.
- Each sub-question must have a clear purpose.
- Success criteria must describe what evidence is needed before the final report can be trusted.
- Return only data that matches the supplied JSON schema.
"""


class PlannerService:
    def __init__(self, llm: StructuredLLM) -> None:
        self.llm = llm

    def create_plan(self, query: str) -> ResearchPlan:
        normalized = " ".join(query.strip().split())
        if len(normalized) < 8:
            raise ValueError("Research query is too short")

        return self.llm.generate_structured(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=f"Research request:\n{normalized}",
            schema=ResearchPlan,
        )
