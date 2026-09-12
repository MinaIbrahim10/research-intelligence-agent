import json

import pytest
from pydantic import BaseModel

from app.providers.ollama import (
    OllamaStructuredLLM,
)


class ExampleOutput(BaseModel):
    answer: str


class FakeResponse:

    status_code = 200
    text = ""

    def __init__(
        self,
        body,
    ):
        self._body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


class FakeHTTPClient:

    last_payload = None

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

    def post(
        self,
        url,
        *,
        json,
    ):
        FakeHTTPClient.last_payload = (
            json
        )

        return FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": (
                        '{"answer":"OK"}'
                    ),
                    "thinking": "",
                },
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 50,
                "eval_count": 8,
            }
        )


def test_structured_ollama_disables_thinking(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.providers.ollama.httpx.Client",
        FakeHTTPClient,
    )

    llm = OllamaStructuredLLM(
        base_url=(
            "http://localhost:11434"
        ),
        model="gemma4:e4b",
    )

    result = llm.generate_structured(
        system_prompt="System",
        user_prompt="Return OK",
        schema=ExampleOutput,
    )

    assert result.answer == "OK"

    payload = (
        FakeHTTPClient.last_payload
    )

    assert payload["think"] is False

    assert (
        payload["options"]["temperature"]
        == 0
    )

    assert (
        payload["options"]["num_predict"]
        == 3072
    )

    assert (
        payload["format"]["type"]
        == "object"
    )


class EmptyHTTPClient:

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

    def post(
        self,
        url,
        *,
        json,
    ):
        return FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "thinking": (
                        "Internal reasoning"
                    ),
                },
                "done": True,
                "done_reason": "length",
                "prompt_eval_count": 5000,
                "eval_count": 2048,
            }
        )


def test_empty_content_has_useful_diagnostics(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.providers.ollama.httpx.Client",
        EmptyHTTPClient,
    )

    llm = OllamaStructuredLLM(
        base_url=(
            "http://localhost:11434"
        ),
        model="gemma4:e4b",
    )

    with pytest.raises(
        ValueError,
        match="done_reason=length",
    ):
        llm.generate_structured(
            system_prompt="System",
            user_prompt="Research",
            schema=ExampleOutput,
        )
