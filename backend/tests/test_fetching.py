import pytest

from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.services.fetching import (
    SourceFetchService,
)
from app.tools.web_fetcher import (
    FetchedPage,
    UnsafeURL,
    validate_public_url,
)


class FakePageFetcher:

    def fetch(
        self,
        url: str,
    ) -> FetchedPage:

        html = """
        <html>
          <body>
            <nav>Navigation noise</nav>
            <article>
              <h1>Technical Documentation</h1>
              <p>
                The runtime stores durable state
                using checkpoints so workflows
                can continue after interruption.
              </p>
              <p>
                Tool calls and node transitions
                are recorded for observability.
              </p>
            </article>
            <footer>Footer noise</footer>
          </body>
        </html>
        """

        return FetchedPage(
            final_url=url,
            content_type="text/html",
            html=html,
            bytes_downloaded=len(
                html.encode()
            ),
        )


def make_plan():

    return ResearchPlan(
        objective="Evaluate agent systems",
        questions=[
            ResearchQuestion(
                id="q1",
                question="How is state persisted?",
                purpose="Evaluate persistence",
                priority="high",
            ),
            ResearchQuestion(
                id="q2",
                question="How are failures handled?",
                purpose="Evaluate reliability",
                priority="high",
            ),
            ResearchQuestion(
                id="q3",
                question="How is tracing handled?",
                purpose="Evaluate observability",
                priority="medium",
            ),
        ],
        suggested_source_types=[
            "official documentation",
            "repositories",
        ],
        freshness_required=True,
        freshness_reason="APIs change",
        success_criteria=[
            "Use direct evidence",
            "Use reliable sources",
        ],
    )


def make_corpus():

    results = []

    for index in range(
        1,
        4,
    ):
        results.append(
            SearchResult(
                id=f"s{index}",
                title=f"Source {index}",
                url=(
                    "https://example.com/"
                    f"source-{index}"
                ),
                content="Search snippet",
                domain="example.com",
                source_category=(
                    "documentation"
                ),
                provider_score=0.9,
                authority_score=0.98,
                final_score=0.944,
                question_ids=[
                    f"q{index}"
                ],
            )
        )

    return SearchCorpus(
        total_queries=3,
        unique_sources=3,
        results=results,
    )


def test_source_fetcher_extracts_main_content():

    result = SourceFetchService(
        FakePageFetcher(),
        max_sources_per_question=1,
    ).fetch_sources(
        make_plan(),
        make_corpus(),
    )

    assert result.attempted_sources == 3
    assert result.fetched_sources == 3
    assert result.failed_sources == 0

    assert (
        "durable state"
        in result.results[0].content
    )


def test_localhost_url_is_rejected():

    with pytest.raises(
        UnsafeURL
    ):
        validate_public_url(
            "http://127.0.0.1/test"
        )


def test_localhost_name_is_rejected():

    with pytest.raises(
        UnsafeURL
    ):
        validate_public_url(
            "http://localhost/test"
        )
