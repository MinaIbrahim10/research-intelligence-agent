from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.services.searching import (
    build_research_search_query,
    classify_source,
)


def make_plan():

    return ResearchPlan(
        objective=(
            "Compare LangGraph and CrewAI "
            "for reliable production systems."
        ),
        questions=[
            ResearchQuestion(
                id="q1",
                question=(
                    "How is state managed?"
                ),
                purpose=(
                    "Compare persistence."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question=(
                    "How are failures handled?"
                ),
                purpose=(
                    "Compare reliability."
                ),
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question=(
                    "What is the learning curve?"
                ),
                purpose=(
                    "Compare developer experience."
                ),
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "Technical Documentation",
            "GitHub Repositories",
        ],
        freshness_required=True,
        freshness_reason=(
            "Frameworks evolve rapidly."
        ),
        success_criteria=[
            "Compare both frameworks.",
            "Use primary evidence.",
        ],
    )


def test_query_keeps_overall_framework_context():

    plan = make_plan()

    query = build_research_search_query(
        plan,
        plan.questions[0],
    )

    assert "LangGraph" in query
    assert "CrewAI" in query
    assert "state managed" in query
    assert "official documentation" in query
    assert "GitHub repository" in query


def test_developer_ibm_article_not_automatic_docs():

    category = classify_source(
        "https://developer.ibm.com/"
        "articles/example"
    )

    assert category == "general_web"


def test_docs_subdomain_is_documentation():

    category = classify_source(
        "https://docs.example.com/"
        "agents/state"
    )

    assert category == "documentation"
