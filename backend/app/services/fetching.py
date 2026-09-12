from __future__ import annotations

from typing import Protocol

from trafilatura import extract

from app.schemas.planner import (
    ResearchPlan,
)
from app.schemas.search import (
    SearchCorpus,
    SearchResult,
)
from app.schemas.source import (
    FetchedSource,
    SourceContentCorpus,
)
from app.tools.web_fetcher import (
    FetchedPage,
)


class PageFetcher(Protocol):

    def fetch(
        self,
        url: str,
    ) -> FetchedPage:
        ...


class SourceFetchService:

    def __init__(
        self,
        fetcher: PageFetcher,
        *,
        max_sources_per_question: int = 3,
        min_content_chars: int = 120,
        max_content_chars: int = 20_000,
    ) -> None:

        if max_sources_per_question < 1:
            raise ValueError(
                "max_sources_per_question "
                "must be at least 1"
            )

        if min_content_chars < 50:
            raise ValueError(
                "min_content_chars "
                "must be at least 50"
            )

        if (
            max_content_chars
            < min_content_chars
        ):
            raise ValueError(
                "max_content_chars must be "
                "greater than min_content_chars"
            )

        self.fetcher = fetcher

        self.max_sources_per_question = (
            max_sources_per_question
        )

        self.min_content_chars = (
            min_content_chars
        )

        self.max_content_chars = (
            max_content_chars
        )

    def _select_sources(
        self,
        plan: ResearchPlan,
        corpus: SearchCorpus,
    ) -> list[SearchResult]:

        selected: dict[
            str,
            SearchResult,
        ] = {}

        for question in plan.questions:

            candidates = [
                source
                for source in corpus.results
                if (
                    question.id
                    in source.question_ids
                )
            ]

            candidates.sort(
                key=lambda source: (
                    source.final_score,
                    source.provider_score,
                ),
                reverse=True,
            )

            for source in candidates[
                :self.max_sources_per_question
            ]:
                selected.setdefault(
                    source.id,
                    source,
                )

        return list(
            selected.values()
        )

    def _extract_main_text(
        self,
        page: FetchedPage,
    ) -> str:

        text = extract(
            page.html,
            url=page.final_url,
            output_format="txt",
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )

        if (
            not text
            or len(text.strip())
            < self.min_content_chars
        ):
            text = extract(
                page.html,
                url=page.final_url,
                output_format="txt",
                include_comments=False,
                include_tables=True,
                favor_recall=True,
            )

        if not text:
            return ""

        return (
            text.strip()[
                :self.max_content_chars
            ]
        )

    def fetch_sources(
        self,
        plan: ResearchPlan,
        corpus: SearchCorpus,
    ) -> SourceContentCorpus:

        selected_sources = (
            self._select_sources(
                plan,
                corpus,
            )
        )

        results: list[
            FetchedSource
        ] = []

        for source in selected_sources:

            try:
                page = self.fetcher.fetch(
                    str(source.url)
                )

                content = (
                    self._extract_main_text(
                        page
                    )
                )

                if (
                    len(content)
                    < self.min_content_chars
                ):
                    raise RuntimeError(
                        "Insufficient extracted "
                        "main content"
                    )

                results.append(
                    FetchedSource(
                        source_id=source.id,
                        title=source.title,
                        url=source.url,
                        final_url=(
                            page.final_url
                        ),
                        question_ids=(
                            source.question_ids
                        ),
                        source_category=(
                            source.source_category
                        ),
                        final_score=(
                            source.final_score
                        ),
                        content=content,
                        content_chars=len(
                            content
                        ),
                        content_type=(
                            page.content_type
                        ),
                        status="fetched",
                        error=None,
                    )
                )

            except Exception as exc:

                results.append(
                    FetchedSource(
                        source_id=source.id,
                        title=source.title,
                        url=source.url,
                        final_url=None,
                        question_ids=(
                            source.question_ids
                        ),
                        source_category=(
                            source.source_category
                        ),
                        final_score=(
                            source.final_score
                        ),
                        content="",
                        content_chars=0,
                        content_type=None,
                        status="failed",
                        error=str(exc)[:500],
                    )
                )

        fetched_count = sum(
            1
            for source in results
            if source.status == "fetched"
        )

        failed_count = (
            len(results)
            - fetched_count
        )

        return SourceContentCorpus(
            attempted_sources=len(
                results
            ),
            fetched_sources=(
                fetched_count
            ),
            failed_sources=(
                failed_count
            ),
            results=results,
        )
