from fastapi import FastAPI

from app.api.research import (
    router as research_router,
)

from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "Evidence-first agentic "
        "research backend."
    ),
)


@app.get(
    "/health",
    tags=["system"],
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "milestone": "search-v1",
    }


app.include_router(
    research_router
)
