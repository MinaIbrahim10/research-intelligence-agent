import pytest
from pydantic import ValidationError

from app.schemas.planner import ResearchPlan, ResearchQuestion


def _question(qid: str, text: str) -> ResearchQuestion:
    return ResearchQuestion(
        id=qid,
        question=text,
        purpose="Provide evidence for this part of the research question.",
        priority="medium",
    )


def test_research_plan_rejects_duplicate_question_ids():
    with pytest.raises(ValidationError, match="ids must be unique"):
        ResearchPlan(
            objective="Build a trustworthy comparison using current primary evidence.",
            questions=[
                _question("q1", "What does framework A support in production systems?"),
                _question("q1", "What does framework B support in production systems?"),
                _question("q3", "What limitations are documented by maintainers today?"),
            ],
            suggested_source_types=["official docs", "official repositories"],
            freshness_required=True,
            freshness_reason="The frameworks change frequently over time.",
            success_criteria=["Primary evidence exists", "Limitations are captured"],
        )


def test_research_plan_rejects_duplicate_question_text():
    duplicated = "What production persistence features are officially documented?"
    with pytest.raises(ValidationError, match="questions must be unique"):
        ResearchPlan(
            objective="Build a trustworthy comparison using current primary evidence.",
            questions=[
                _question("q1", duplicated),
                _question("q2", duplicated),
                _question("q3", "What limitations are documented by maintainers today?"),
            ],
            suggested_source_types=["official docs", "official repositories"],
            freshness_required=True,
            freshness_reason="The frameworks change frequently over time.",
            success_criteria=["Primary evidence exists", "Limitations are captured"],
        )
