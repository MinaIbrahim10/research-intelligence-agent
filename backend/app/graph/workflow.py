from app.agents.consolidator import (
    build_consolidator_node,
)
from app.agents.fetcher import (
    build_fetcher_node,
)
from app.agents.planner import (
    build_planner_node,
)
from app.agents.relevance import (
    build_relevance_node,
)
from app.agents.reporter import (
    build_reporter_node,
)
from app.agents.researcher import (
    build_researcher_node,
)
from app.agents.searcher import (
    build_search_node,
)
from app.agents.verifier import (
    build_verifier_node,
)

from app.graph.state import (
    ResearchState,
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


def _graph_types():

    try:
        from langgraph.graph import (
            END,
            START,
            StateGraph,
        )

    except ImportError as exc:
        raise RuntimeError(
            "LangGraph is not installed. "
            "Install project dependencies."
        ) from exc

    return END, START, StateGraph


def build_planner_graph(
    service: PlannerService,
):

    END, START, StateGraph = (
        _graph_types()
    )

    builder = StateGraph(
        ResearchState
    )

    builder.add_node(
        "planner",
        build_planner_node(
            service
        ),
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        END,
    )

    return builder.compile()


def build_research_graph(
    planner_service: PlannerService,
    search_service: SearchService,
):

    END, START, StateGraph = (
        _graph_types()
    )

    builder = StateGraph(
        ResearchState
    )

    builder.add_node(
        "planner",
        build_planner_node(
            planner_service
        ),
    )

    builder.add_node(
        "search",
        build_search_node(
            search_service
        ),
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "search",
    )

    builder.add_edge(
        "search",
        END,
    )

    return builder.compile()


def build_evidence_graph(
    planner_service: PlannerService,
    search_service: SearchService,
    fetch_service: SourceFetchService,
    research_service: ResearchService,
    relevance_service: EvidenceRelevanceService,
):

    END, START, StateGraph = (
        _graph_types()
    )

    builder = StateGraph(
        ResearchState
    )

    builder.add_node(
        "planner",
        build_planner_node(
            planner_service
        ),
    )

    builder.add_node(
        "search",
        build_search_node(
            search_service
        ),
    )

    builder.add_node(
        "fetch_sources",
        build_fetcher_node(
            fetch_service
        ),
    )

    builder.add_node(
        "researcher",
        build_researcher_node(
            research_service
        ),
    )

    builder.add_node(
        "relevance",
        build_relevance_node(
            relevance_service
        ),
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "search",
    )

    builder.add_edge(
        "search",
        "fetch_sources",
    )

    builder.add_edge(
        "fetch_sources",
        "researcher",
    )

    builder.add_edge(
        "researcher",
        "relevance",
    )

    builder.add_edge(
        "relevance",
        END,
    )

    return builder.compile()


def build_verification_graph(
    planner_service: PlannerService,
    search_service: SearchService,
    fetch_service: SourceFetchService,
    research_service: ResearchService,
    relevance_service: EvidenceRelevanceService,
    consolidation_service: ClaimConsolidationService,
    verification_service: VerificationService,
):

    END, START, StateGraph = (
        _graph_types()
    )

    builder = StateGraph(
        ResearchState
    )

    builder.add_node(
        "planner",
        build_planner_node(
            planner_service
        ),
    )

    builder.add_node(
        "search",
        build_search_node(
            search_service
        ),
    )

    builder.add_node(
        "fetch_sources",
        build_fetcher_node(
            fetch_service
        ),
    )

    builder.add_node(
        "researcher",
        build_researcher_node(
            research_service
        ),
    )

    builder.add_node(
        "relevance",
        build_relevance_node(
            relevance_service
        ),
    )

    builder.add_node(
        "consolidator",
        build_consolidator_node(
            consolidation_service
        ),
    )

    builder.add_node(
        "verifier",
        build_verifier_node(
            verification_service
        ),
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "search",
    )

    builder.add_edge(
        "search",
        "fetch_sources",
    )

    builder.add_edge(
        "fetch_sources",
        "researcher",
    )

    builder.add_edge(
        "researcher",
        "relevance",
    )

    builder.add_edge(
        "relevance",
        "consolidator",
    )

    builder.add_edge(
        "consolidator",
        "verifier",
    )

    builder.add_edge(
        "verifier",
        END,
    )

    return builder.compile()



def build_report_graph(
    planner_service: PlannerService,
    search_service: SearchService,
    fetch_service: SourceFetchService,
    research_service: ResearchService,
    relevance_service: EvidenceRelevanceService,
    consolidation_service: ClaimConsolidationService,
    verification_service: VerificationService,
    report_service: ReportService,
):

    END, START, StateGraph = (
        _graph_types()
    )

    builder = StateGraph(
        ResearchState
    )

    builder.add_node(
        "planner",
        build_planner_node(
            planner_service
        ),
    )

    builder.add_node(
        "search",
        build_search_node(
            search_service
        ),
    )

    builder.add_node(
        "fetch_sources",
        build_fetcher_node(
            fetch_service
        ),
    )

    builder.add_node(
        "researcher",
        build_researcher_node(
            research_service
        ),
    )

    builder.add_node(
        "relevance",
        build_relevance_node(
            relevance_service
        ),
    )

    builder.add_node(
        "consolidator",
        build_consolidator_node(
            consolidation_service
        ),
    )

    builder.add_node(
        "verifier",
        build_verifier_node(
            verification_service
        ),
    )

    builder.add_node(
        "reporter",
        build_reporter_node(
            report_service
        ),
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "search",
    )

    builder.add_edge(
        "search",
        "fetch_sources",
    )

    builder.add_edge(
        "fetch_sources",
        "researcher",
    )

    builder.add_edge(
        "researcher",
        "relevance",
    )

    builder.add_edge(
        "relevance",
        "consolidator",
    )

    builder.add_edge(
        "consolidator",
        "verifier",
    )

    builder.add_edge(
        "verifier",
        "reporter",
    )

    builder.add_edge(
        "reporter",
        END,
    )

    return builder.compile()
