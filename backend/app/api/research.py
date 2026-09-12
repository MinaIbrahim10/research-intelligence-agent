from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.dependencies import (
    get_report_service,
    get_consolidation_service,
    get_fetch_service,
    get_planner_service,
    get_relevance_service,
    get_research_service,
    get_search_service,
    get_verification_service,
)

from app.graph.workflow import (
    build_evidence_graph,
    build_planner_graph,
    build_research_graph,
    build_report_graph,
    build_verification_graph,
)

from app.schemas.evidence import (
    EvidenceResponse,
)
from app.schemas.planner import (
    PlanRequest,
    PlanResponse,
)
from app.schemas.report import (
    ReportResponse,
)
from app.schemas.search import (
    SearchResponse,
)

from app.schemas.verification import (
    VerificationResponse,
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


router = APIRouter(
    prefix="/api/v1/research",
    tags=["research"],
)


@router.post(
    "/plan",
    response_model=PlanResponse,
)
def create_research_plan(
    request: PlanRequest,
    planner_service: PlannerService = Depends(
        get_planner_service
    ),
) -> PlanResponse:

    graph = build_planner_graph(
        planner_service
    )

    state = graph.invoke(
        {
            "query": request.query,
            "errors": [],
        }
    )

    errors = state.get(
        "errors",
        [],
    )

    if errors:
        raise HTTPException(
            status_code=502,
            detail=errors[0],
        )

    plan = state.get(
        "plan"
    )

    if plan is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Planner completed "
                "without a plan"
            ),
        )

    return PlanResponse(
        query=request.query,
        plan=plan,
    )


@router.post(
    "/search",
    response_model=SearchResponse,
)
def run_research_search(
    request: PlanRequest,
    planner_service: PlannerService = Depends(
        get_planner_service
    ),
    search_service: SearchService = Depends(
        get_search_service
    ),
) -> SearchResponse:

    graph = build_research_graph(
        planner_service,
        search_service,
    )

    state = graph.invoke(
        {
            "query": request.query,
            "errors": [],
        }
    )

    errors = state.get(
        "errors",
        [],
    )

    if errors:
        raise HTTPException(
            status_code=502,
            detail=errors[0],
        )

    plan = state.get(
        "plan"
    )

    corpus = state.get(
        "corpus"
    )

    if (
        plan is None
        or corpus is None
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Search graph returned "
                "incomplete state"
            ),
        )

    return SearchResponse(
        query=request.query,
        plan=plan,
        corpus=corpus,
    )


@router.post(
    "/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_200_OK,
)
def extract_research_evidence(
    request: PlanRequest,

    planner_service: PlannerService = Depends(
        get_planner_service
    ),

    search_service: SearchService = Depends(
        get_search_service
    ),

    fetch_service: SourceFetchService = Depends(
        get_fetch_service
    ),

    research_service: ResearchService = Depends(
        get_research_service
    ),

    relevance_service: EvidenceRelevanceService = Depends(
        get_relevance_service
    ),
) -> EvidenceResponse:

    graph = build_evidence_graph(
        planner_service,
        search_service,
        fetch_service,
        research_service,
        relevance_service,
    )

    state = graph.invoke(
        {
            "query": request.query,
            "errors": [],
        }
    )

    errors = state.get(
        "errors",
        [],
    )

    if errors:
        raise HTTPException(
            status_code=502,
            detail=errors[0],
        )

    plan = state.get(
        "plan"
    )

    corpus = state.get(
        "corpus"
    )

    source_corpus = state.get(
        "source_corpus"
    )

    evidence = state.get(
        "evidence"
    )

    if (
        plan is None
        or corpus is None
        or source_corpus is None
        or evidence is None
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Evidence graph returned "
                "incomplete state"
            ),
        )

    return EvidenceResponse(
        query=request.query,
        plan=plan,
        corpus=corpus,
        sources=source_corpus,
        evidence=evidence,
    )


@router.post(
    "/verify",
    response_model=VerificationResponse,
)
def verify_research_evidence(
    request: PlanRequest,

    planner_service: PlannerService = Depends(
        get_planner_service
    ),

    search_service: SearchService = Depends(
        get_search_service
    ),

    fetch_service: SourceFetchService = Depends(
        get_fetch_service
    ),

    research_service: ResearchService = Depends(
        get_research_service
    ),

    relevance_service: EvidenceRelevanceService = Depends(
        get_relevance_service
    ),

    consolidation_service: ClaimConsolidationService = Depends(
        get_consolidation_service
    ),

    verification_service: VerificationService = Depends(
        get_verification_service
    ),
) -> VerificationResponse:

    graph = build_verification_graph(
        planner_service,
        search_service,
        fetch_service,
        research_service,
        relevance_service,
        consolidation_service,
        verification_service,
    )

    state = graph.invoke(
        {
            "query": request.query,
            "errors": [],
        }
    )

    errors = state.get(
        "errors",
        [],
    )

    if errors:
        raise HTTPException(
            status_code=502,
            detail=errors[0],
        )

    plan = state.get(
        "plan"
    )

    corpus = state.get(
        "corpus"
    )

    source_corpus = state.get(
        "source_corpus"
    )

    evidence = state.get(
        "evidence"
    )

    claims = state.get(
        "claims"
    )

    verification = state.get(
        "verification"
    )

    if (
        plan is None
        or corpus is None
        or source_corpus is None
        or evidence is None
        or claims is None
        or verification is None
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Verification graph returned "
                "incomplete state"
            ),
        )

    return VerificationResponse(
        query=request.query,
        plan=plan,
        corpus=corpus,
        sources=source_corpus,
        evidence=evidence,
        claims=claims,
        verification=verification,
    )



@router.post(
    "/report",
    response_model=ReportResponse,
)
def generate_research_report(
    request: PlanRequest,

    planner_service: PlannerService = Depends(
        get_planner_service
    ),

    search_service: SearchService = Depends(
        get_search_service
    ),

    fetch_service: SourceFetchService = Depends(
        get_fetch_service
    ),

    research_service: ResearchService = Depends(
        get_research_service
    ),

    relevance_service: EvidenceRelevanceService = Depends(
        get_relevance_service
    ),

    consolidation_service: ClaimConsolidationService = Depends(
        get_consolidation_service
    ),

    verification_service: VerificationService = Depends(
        get_verification_service
    ),

    report_service: ReportService = Depends(
        get_report_service
    ),
) -> ReportResponse:

    graph = build_report_graph(
        planner_service,
        search_service,
        fetch_service,
        research_service,
        relevance_service,
        consolidation_service,
        verification_service,
        report_service,
    )

    state = graph.invoke(
        {
            "query": request.query,
            "errors": [],
        }
    )

    errors = state.get(
        "errors",
        [],
    )

    if errors:
        raise HTTPException(
            status_code=502,
            detail=errors[0],
        )

    plan = state.get("plan")
    corpus = state.get("corpus")
    source_corpus = state.get(
        "source_corpus"
    )
    evidence = state.get("evidence")
    claims = state.get("claims")
    verification = state.get(
        "verification"
    )
    report = state.get("report")

    if any(
        item is None
        for item in (
            plan,
            corpus,
            source_corpus,
            evidence,
            claims,
            verification,
            report,
        )
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Report graph returned "
                "incomplete state"
            ),
        )

    return ReportResponse(
        query=request.query,
        plan=plan,
        corpus=corpus,
        sources=source_corpus,
        evidence=evidence,
        claims=claims,
        verification=verification,
        report=report,
    )



@router.post(
    "/report/stream",
)
def stream_research_report(
    request: PlanRequest,

    planner_service: PlannerService = Depends(
        get_planner_service
    ),

    search_service: SearchService = Depends(
        get_search_service
    ),

    fetch_service: SourceFetchService = Depends(
        get_fetch_service
    ),

    research_service: ResearchService = Depends(
        get_research_service
    ),

    relevance_service: EvidenceRelevanceService = Depends(
        get_relevance_service
    ),

    consolidation_service: ClaimConsolidationService = Depends(
        get_consolidation_service
    ),

    verification_service: VerificationService = Depends(
        get_verification_service
    ),

    report_service: ReportService = Depends(
        get_report_service
    ),
):
    import json

    from fastapi.responses import (
        StreamingResponse,
    )

    graph = build_report_graph(
        planner_service,
        search_service,
        fetch_service,
        research_service,
        relevance_service,
        consolidation_service,
        verification_service,
        report_service,
    )

    stages = [
        {
            "node": "planner",
            "label": "Planning research questions",
            "detail": (
                "Breaking the objective into "
                "focused research questions."
            ),
        },
        {
            "node": "search",
            "label": "Searching the web",
            "detail": (
                "Finding and ranking relevant "
                "sources."
            ),
        },
        {
            "node": "fetch_sources",
            "label": "Fetching full pages",
            "detail": (
                "Retrieving source content "
                "for evidence extraction."
            ),
        },
        {
            "node": "researcher",
            "label": "Extracting evidence",
            "detail": (
                "Extracting grounded claims "
                "and exact supporting excerpts."
            ),
        },
        {
            "node": "relevance",
            "label": "Filtering relevance",
            "detail": (
                "Removing evidence that does "
                "not directly answer the "
                "research questions."
            ),
        },
        {
            "node": "consolidator",
            "label": "Consolidating claims",
            "detail": (
                "Grouping equivalent findings "
                "into traceable claim families."
            ),
        },
        {
            "node": "verifier",
            "label": "Verifying claims",
            "detail": (
                "Checking corroboration, "
                "conflicts and confidence."
            ),
        },
        {
            "node": "reporter",
            "label": "Building final report",
            "detail": (
                "Calculating coverage and "
                "assembling the cited report."
            ),
        },
    ]

    stage_lookup = {
        stage["node"]: index
        for index, stage
        in enumerate(stages)
    }

    def encode_event(
        event_name: str,
        payload: dict,
    ) -> str:

        return (
            f"event: {event_name}\n"
            "data: "
            + json.dumps(
                payload,
                ensure_ascii=False,
            )
            + "\n\n"
        )

    def progress_payload(
        index: int,
        status: str,
    ) -> dict:

        stage = stages[index]

        return {
            "stage": stage["node"],
            "label": stage["label"],
            "detail": stage["detail"],
            "status": status,
            "index": index,
            "total": len(stages),
            "progress": round(
                (
                    index
                    + (
                        1
                        if status == "complete"
                        else 0
                    )
                )
                / len(stages),
                3,
            ),
        }

    def event_stream():

        state = {
            "query": request.query,
            "errors": [],
        }

        # Immediate real state:
        # the graph is about to execute planner.
        yield encode_event(
            "progress",
            progress_payload(
                0,
                "running",
            ),
        )

        try:

            for chunk in graph.stream(
                state,
                stream_mode="updates",
            ):

                if not isinstance(
                    chunk,
                    dict,
                ):
                    continue

                for (
                    node_name,
                    update,
                ) in chunk.items():

                    if isinstance(
                        update,
                        dict,
                    ):
                        state.update(
                            update
                        )

                    stage_index = (
                        stage_lookup.get(
                            node_name
                        )
                    )

                    if (
                        stage_index
                        is None
                    ):
                        continue

                    # Node has ACTUALLY
                    # completed.
                    yield encode_event(
                        "progress",
                        progress_payload(
                            stage_index,
                            "complete",
                        ),
                    )

                    errors = state.get(
                        "errors",
                        [],
                    )

                    if errors:

                        yield encode_event(
                            "error",
                            {
                                "detail": (
                                    errors[0]
                                ),
                                "stage": (
                                    node_name
                                ),
                            },
                        )

                        return

                    next_index = (
                        stage_index + 1
                    )

                    if (
                        next_index
                        < len(stages)
                    ):

                        # The graph has now
                        # moved to the next
                        # real stage.
                        yield encode_event(
                            "progress",
                            progress_payload(
                                next_index,
                                "running",
                            ),
                        )

            plan = state.get(
                "plan"
            )

            corpus = state.get(
                "corpus"
            )

            source_corpus = state.get(
                "source_corpus"
            )

            evidence = state.get(
                "evidence"
            )

            claims = state.get(
                "claims"
            )

            verification = state.get(
                "verification"
            )

            report = state.get(
                "report"
            )

            if any(
                value is None
                for value in (
                    plan,
                    corpus,
                    source_corpus,
                    evidence,
                    claims,
                    verification,
                    report,
                )
            ):

                yield encode_event(
                    "error",
                    {
                        "detail": (
                            "Streaming graph "
                            "returned incomplete "
                            "state."
                        ),
                    },
                )

                return

            response = ReportResponse(
                query=request.query,
                plan=plan,
                corpus=corpus,
                sources=source_corpus,
                evidence=evidence,
                claims=claims,
                verification=verification,
                report=report,
            )

            yield encode_event(
                "result",
                response.model_dump(
                    mode="json",
                ),
            )

        except GeneratorExit:
            return

        except Exception as exc:

            yield encode_event(
                "error",
                {
                    "detail": (
                        "Research streaming "
                        "failed: "
                        f"{exc}"
                    ),
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type=(
            "text/event-stream"
        ),
        headers={
            "Cache-Control": (
                "no-cache"
            ),
            "Connection": (
                "keep-alive"
            ),
            "X-Accel-Buffering": (
                "no"
            ),
        },
    )
