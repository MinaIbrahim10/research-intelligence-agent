from functools import lru_cache

from app.config import (
    get_settings,
)

from app.providers.factory import (
    build_llm,
)

from app.services.consolidation import (
    ClaimConsolidationService,
)
from app.services.fetching import (
    SourceFetchService,
)
from app.services.planning import (
    PlannerService,
)
from app.services.relevance import (
    EvidenceRelevanceService,
)
from app.services.researching import (
    ResearchService,
)

from app.services.reporting import (
    ReportService,
)
from app.services.searching import (
    SearchService,
)
from app.services.verification import (
    VerificationService,
)

from app.tools.searxng_search import (
    SearXNGSearchClient,
)
from app.tools.web_fetcher import (
    SafeWebFetcher,
)


@lru_cache
def get_planner_service() -> PlannerService:

    settings = get_settings()

    return PlannerService(
        build_llm(settings)
    )


@lru_cache
def get_search_service() -> SearchService:

    settings = get_settings()

    return SearchService(
        SearXNGSearchClient(
            base_url=(
                settings.searxng_base_url
            ),
            timeout_seconds=(
                settings
                .searxng_timeout_seconds
            ),
        ),
        max_results_per_query=(
            settings
            .search_max_results_per_query
        ),
    )


@lru_cache
def get_fetch_service() -> SourceFetchService:

    settings = get_settings()

    return SourceFetchService(
        SafeWebFetcher(
            timeout_seconds=(
                settings
                .source_fetch_timeout_seconds
            ),
            max_bytes=(
                settings
                .source_fetch_max_bytes
            ),
        ),
        max_sources_per_question=(
            settings
            .source_fetch_max_sources_per_question
        ),
    )


@lru_cache
def get_research_service() -> ResearchService:

    settings = get_settings()

    return ResearchService(
        build_llm(settings)
    )


@lru_cache
def get_relevance_service() -> EvidenceRelevanceService:

    settings = get_settings()

    return EvidenceRelevanceService(
        build_llm(settings),
        acceptance_threshold=0.70,
    )


@lru_cache
def get_consolidation_service() -> ClaimConsolidationService:

    settings = get_settings()

    return ClaimConsolidationService(
        build_llm(settings)
    )


@lru_cache
def get_verification_service() -> VerificationService:

    settings = get_settings()

    return VerificationService(
        build_llm(settings)
    )



@lru_cache
def get_report_service() -> ReportService:

    return ReportService()
