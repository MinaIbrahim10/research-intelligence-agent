from app.tools.searxng_search import (
    SearXNGSearchClient,
)


class FakeResponse:

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "query": "LangGraph agents",
            "results": [
                {
                    "title": "LangGraph",
                    "url": (
                        "https://www.langchain.com/"
                        "langgraph"
                    ),
                    "content": (
                        "Agent orchestration framework"
                    ),
                    "score": 1.0,
                    "engine": "brave",
                    "publishedDate": None,
                },
                {
                    "title": "Second result",
                    "url": (
                        "https://example.com/test"
                    ),
                    "content": "Example",
                    "score": 0.8,
                    "engine": "brave",
                },
            ],
        }


class FakeHTTPClient:

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    def get(
        self,
        url,
        *,
        params,
        headers,
    ):

        assert url == (
            "http://127.0.0.1:8080/search"
        )

        assert params["q"] == (
            "LangGraph agents"
        )

        assert params["format"] == "json"

        assert (
            headers["Accept"]
            == "application/json"
        )

        return FakeResponse()


def test_searxng_client_parses_results(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.tools.searxng_search.httpx.Client",
        FakeHTTPClient,
    )

    client = SearXNGSearchClient(
        "http://127.0.0.1:8080/"
    )

    results = client.search(
        "  LangGraph   agents  ",
        max_results=1,
    )

    assert len(results) == 1

    assert (
        results[0].title
        == "LangGraph"
    )

    assert (
        results[0].engine
        == "brave"
    )

    assert results[0].score == 1.0
