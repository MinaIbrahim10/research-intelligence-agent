from __future__ import annotations

from typing import Protocol
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from app.schemas.planner import (
    ResearchPlan,
    ResearchQuestion,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.tools.searxng_search import (
    RawSearchResult,
)


class SearchClient(Protocol):

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[RawSearchResult]:
        ...


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "ref",
    "ref_src",
    "source",
}

LOW_AUTHORITY_DOMAINS = {
    "medium.com",
    "reddit.com",
    "quora.com",
    "dev.to",
    "daily.dev",
}

HIGH_AUTHORITY_NEWS_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
}

ACADEMIC_DOMAINS = {
    "arxiv.org",
    "openreview.net",
    "doi.org",
    "pubmed.ncbi.nlm.nih.gov",
    "acm.org",
    "ieee.org",
}

REPOSITORY_DOMAINS = {
    "github.com",
    "gitlab.com",
    "bitbucket.org",
}


def canonicalize_url(
    url: str,
) -> str:

    parts = urlsplit(
        url.strip()
    )

    scheme = (
        parts.scheme.lower()
        or "https"
    )

    hostname = (
        parts.hostname
        or ""
    ).lower()

    port = parts.port

    if (
        port is not None
        and not (
            scheme == "https"
            and port == 443
        )
        and not (
            scheme == "http"
            and port == 80
        )
    ):
        netloc = (
            f"{hostname}:{port}"
        )
    else:
        netloc = hostname

    path = parts.path or "/"

    if (
        path != "/"
        and path.endswith("/")
    ):
        path = path.rstrip("/")

    cleaned_query = []

    for key, value in parse_qsl(
        parts.query,
        keep_blank_values=True,
    ):

        lowered = key.lower()

        if lowered.startswith(
            "utm_"
        ):
            continue

        if lowered in TRACKING_PARAMS:
            continue

        cleaned_query.append(
            (key, value)
        )

    query = urlencode(
        cleaned_query,
        doseq=True,
    )

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            "",
        )
    )


def get_domain(
    url: str,
) -> str:

    hostname = (
        urlsplit(url).hostname
        or ""
    ).lower()

    if hostname.startswith(
        "www."
    ):
        hostname = hostname[4:]

    return hostname


def classify_source(
    url: str,
) -> str:

    parts = urlsplit(url)

    domain = get_domain(
        url
    )

    path = (
        parts.path
        or ""
    ).lower()

    if (
        domain.endswith(".gov")
        or ".gov." in domain
    ):
        return "government"

    if (
        domain.endswith(".edu")
        or domain.endswith(".ac.uk")
        or domain in ACADEMIC_DOMAINS
    ):
        return "academic"

    if domain in REPOSITORY_DOMAINS:
        return "repository"

    documentation_path = any(
        marker in path
        for marker in (
            "/docs/",
            "/documentation/",
            "/reference/",
            "/api/",
            "/guides/",
        )
    )

    documentation_domain = (
        domain.startswith("docs.")
        or domain.startswith(
            "documentation."
        )
    )

    if (
        documentation_domain
        or documentation_path
    ):
        return "documentation"

    if (
        domain
        in HIGH_AUTHORITY_NEWS_DOMAINS
    ):
        return "news"

    if (
        domain.startswith("news.")
        or domain.startswith(
            "newsroom."
        )
    ):
        return "news"

    return "general_web"


def calculate_authority_score(
    domain: str,
    category: str,
) -> float:

    normalized = (
        domain.lower()
        .removeprefix("www.")
    )

    if category == "government":
        return 1.0

    if category == "documentation":
        return 0.98

    if category == "academic":
        return 0.95

    if category == "repository":
        return 0.90

    if category == "news":

        if (
            normalized
            in HIGH_AUTHORITY_NEWS_DOMAINS
        ):
            return 0.90

        return 0.78

    if (
        normalized
        in LOW_AUTHORITY_DOMAINS
    ):
        return 0.35

    if (
        normalized.startswith(
            "research."
        )
        or normalized.startswith(
            "engineering."
        )
    ):
        return 0.80

    return 0.55


def calculate_final_score(
    provider_score: float,
    authority_score: float,
) -> float:

    value = (
        provider_score * 0.45
        + authority_score * 0.55
    )

    return round(
        max(
            0.0,
            min(
                1.0,
                value,
            ),
        ),
        4,
    )


def _clean_query_part(
    value: str,
) -> str:

    return " ".join(
        value.strip().split()
    )


def build_research_search_query(
    plan: ResearchPlan,
    question: ResearchQuestion,
) -> str:
    """
    Primary high-context query.

    Put the exact sub-question first because
    search engines usually weight earlier
    terms strongly.

    The overall objective preserves entity
    context such as LangGraph vs CrewAI.
    """

    question_text = (
        _clean_query_part(
            question.question
        )
    )

    objective = (
        _clean_query_part(
            plan.objective
        )
    )

    source_types = " ".join(
        plan.suggested_source_types
    ).lower()

    hints: list[str] = []

    if (
        "documentation"
        in source_types
        or "technical"
        in source_types
    ):
        hints.append(
            "official documentation"
        )

    if (
        "github"
        in source_types
        or "repositor"
        in source_types
    ):
        hints.append(
            "GitHub repository"
        )

    hint_text = " ".join(
        hints
    )

    query = (
        f"{question_text} "
        f"{objective} "
        f"{hint_text}"
    ).strip()

    return query[:450]


def build_search_query_variants(
    plan: ResearchPlan,
    question: ResearchQuestion,
) -> list[str]:
    """
    Search from most specific to least
    restrictive.

    This prevents an over-constrained query
    from producing an empty corpus.
    """

    question_text = (
        _clean_query_part(
            question.question
        )
    )

    objective = (
        _clean_query_part(
            plan.objective
        )
    )

    variants = [
        build_research_search_query(
            plan,
            question,
        ),
        (
            f"{question_text} "
            f"{objective}"
        )[:450],
        question_text[:450],
    ]

    unique = []

    seen = set()

    for query in variants:

        normalized = (
            query.strip()
        )

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            normalized
        )

    return unique


class SearchService:

    def __init__(
        self,
        client: SearchClient,
        *,
        max_results_per_query: int = 5,
    ) -> None:

        if max_results_per_query < 1:
            raise ValueError(
                "max_results_per_query "
                "must be at least 1"
            )

        self.client = client

        self.max_results_per_query = (
            max_results_per_query
        )

    def _search_question(
        self,
        plan: ResearchPlan,
        question: ResearchQuestion,
    ) -> list[RawSearchResult]:
        """
        Try progressively broader queries.

        IMPORTANT:
        A broader query is used only when
        the previous query returned zero
        usable results.

        We do not combine every fallback
        variant because that creates source
        drift and unnecessary duplicates.
        """

        variants = (
            build_search_query_variants(
                plan,
                question,
            )
        )

        for query in variants:

            raw_results = (
                self.client.search(
                    query,
                    max_results=(
                        self
                        .max_results_per_query
                    ),
                )
            )

            unique_results: dict[
                str,
                RawSearchResult,
            ] = {}

            for raw in raw_results:

                try:
                    key = canonicalize_url(
                        raw.url
                    )

                except Exception:
                    continue

                existing = (
                    unique_results.get(
                        key
                    )
                )

                if (
                    existing is None
                    or raw.score
                    > existing.score
                ):
                    unique_results[
                        key
                    ] = raw

            if unique_results:

                return list(
                    unique_results.values()
                )[
                    :self.max_results_per_query
                ]

        return []

    def search_plan(
        self,
        plan: ResearchPlan,
    ) -> SearchCorpus:

        by_url: dict[
            str,
            SearchResult,
        ] = {}

        source_counter = 0

        for question in plan.questions:

            raw_results = (
                self._search_question(
                    plan,
                    question,
                )
            )

            for raw in raw_results:

                canonical_url = (
                    canonicalize_url(
                        raw.url
                    )
                )

                domain = get_domain(
                    canonical_url
                )

                category = (
                    classify_source(
                        canonical_url
                    )
                )

                provider_score = max(
                    0.0,
                    min(
                        1.0,
                        float(
                            raw.score
                        ),
                    ),
                )

                authority_score = (
                    calculate_authority_score(
                        domain,
                        category,
                    )
                )

                final_score = (
                    calculate_final_score(
                        provider_score,
                        authority_score,
                    )
                )

                existing = (
                    by_url.get(
                        canonical_url
                    )
                )

                if existing is not None:

                    if (
                        question.id
                        not in
                        existing.question_ids
                    ):
                        existing.question_ids.append(
                            question.id
                        )

                    if (
                        final_score
                        > existing.final_score
                    ):

                        existing.provider_score = (
                            provider_score
                        )

                        existing.authority_score = (
                            authority_score
                        )

                        existing.final_score = (
                            final_score
                        )

                        if raw.content:
                            existing.content = (
                                raw.content
                            )

                    continue

                source_counter += 1

                by_url[
                    canonical_url
                ] = SearchResult(
                    id=(
                        f"s{source_counter}"
                    ),
                    title=raw.title,
                    url=canonical_url,
                    content=(
                        raw.content
                        or ""
                    ),
                    domain=domain,
                    source_category=(
                        category
                    ),
                    provider_score=(
                        provider_score
                    ),
                    authority_score=(
                        authority_score
                    ),
                    final_score=(
                        final_score
                    ),
                    published_date=(
                        raw.published_date
                    ),
                    engine=raw.engine,
                    question_ids=[
                        question.id
                    ],
                )

        results = list(
            by_url.values()
        )

        results.sort(
            key=lambda source: (
                source.final_score,
                source.authority_score,
                source.provider_score,
            ),
            reverse=True,
        )

        return SearchCorpus(
            total_queries=len(
                plan.questions
            ),
            unique_sources=len(
                results
            ),
            results=results,
        )

    def search(
        self,
        plan: ResearchPlan,
    ) -> SearchCorpus:

        return self.search_plan(
            plan
        )
