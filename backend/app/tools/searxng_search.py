from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class RawSearchResult:
    title: str
    url: str
    content: str
    score: float
    published_date: str | None = None
    engine: str | None = None


class SearXNGSearchClient:

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        timeout_seconds: float = 30.0,
    ) -> None:

        normalized_url = base_url.strip().rstrip("/")

        if not normalized_url:
            raise ValueError(
                "SearXNG base URL is required"
            )

        self.base_url = normalized_url
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[RawSearchResult]:

        normalized_query = " ".join(
            query.strip().split()
        )

        if not normalized_query:
            raise ValueError(
                "Search query cannot be empty"
            )

        if max_results < 1:
            raise ValueError(
                "max_results must be at least 1"
            )

        params = {
            "q": normalized_query,
            "format": "json",
            "safesearch": 0,
        }

        try:
            with httpx.Client(
                timeout=self.timeout_seconds
            ) as client:

                response = client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers={
                        "Accept": "application/json",
                    },
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]

            raise RuntimeError(
                "SearXNG search failed with HTTP "
                f"{exc.response.status_code}: {detail}"
            ) from exc

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"SearXNG request failed: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "SearXNG returned invalid JSON"
            ) from exc

        results: list[RawSearchResult] = []

        for item in data.get("results", []):

            title = str(
                item.get("title", "")
            ).strip()

            url = str(
                item.get("url", "")
            ).strip()

            if not title or not url:
                continue

            raw_score = item.get(
                "score",
                0.0,
            )

            try:
                score = float(raw_score)

            except (TypeError, ValueError):
                score = 0.0

            score = max(
                0.0,
                min(score, 1.0),
            )

            engine = item.get("engine")

            if not engine:
                engines = item.get(
                    "engines",
                    [],
                )

                if engines:
                    engine = str(
                        engines[0]
                    )

            published_date = item.get(
                "publishedDate"
            )

            if published_date is not None:
                published_date = str(
                    published_date
                )

            results.append(
                RawSearchResult(
                    title=title,
                    url=url,
                    content=str(
                        item.get(
                            "content",
                            "",
                        )
                        or ""
                    ).strip(),
                    score=score,
                    published_date=published_date,
                    engine=(
                        str(engine)
                        if engine
                        else None
                    ),
                )
            )

            if len(results) >= max_results:
                break

        return results
