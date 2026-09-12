from app.services.searching import (
    calculate_authority_score,
    calculate_final_score,
    classify_source,
)


def test_documentation_has_high_authority():

    category = classify_source(
        "https://docs.example.com/agents"
    )

    score = calculate_authority_score(
        "docs.example.com",
        category,
    )

    assert category == "documentation"
    assert score == 0.98


def test_developer_article_is_general_web():

    category = classify_source(
        "https://developer.ibm.com/articles/test"
    )

    assert category == "general_web"


def test_medium_is_downgraded():

    score = calculate_authority_score(
        "medium.com",
        "general_web",
    )

    assert score == 0.35


def test_authoritative_source_can_beat_high_relevance_blog():

    docs_score = calculate_final_score(
        provider_score=0.70,
        authority_score=0.98,
    )

    blog_score = calculate_final_score(
        provider_score=1.0,
        authority_score=0.35,
    )

    assert docs_score > blog_score


def test_final_score_stays_in_range():

    score = calculate_final_score(
        provider_score=1.0,
        authority_score=1.0,
    )

    assert score == 1.0


def test_docs_subdomain_is_documentation():

    category = classify_source(
        "https://docs.langchain.com/"
        "oss/python/langgraph/overview"
    )

    assert category == "documentation"
