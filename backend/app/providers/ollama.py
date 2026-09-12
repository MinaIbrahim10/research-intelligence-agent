from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from app.providers.base import T


class OllamaStructuredLLM:

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 90.0,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
    ) -> T:

        json_schema = schema.model_json_schema()

        schema_text = json.dumps(
            json_schema,
            ensure_ascii=False,
        )

        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\n"
                        "Return JSON matching this "
                        "schema exactly:\n"
                        f"{schema_text}"
                    ),
                },
            ],
            "format": json_schema,
            "options": {
                "temperature": 0,
                "num_predict": 3072,
            },
        }

        try:

            with httpx.Client(
                timeout=self.timeout_seconds
            ) as client:

                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as exc:

            detail = exc.response.text[:1000]

            raise RuntimeError(
                "Ollama returned HTTP "
                f"{exc.response.status_code}: "
                f"{detail}"
            ) from exc

        except httpx.HTTPError as exc:

            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        try:
            body = response.json()

        except ValueError as exc:

            raise ValueError(
                "Ollama returned invalid HTTP JSON"
            ) from exc

        message = (
            body.get("message")
            or {}
        )

        content = (
            message.get("content")
            or ""
        ).strip()

        if not content:

            thinking = (
                message.get("thinking")
                or ""
            )

            raise ValueError(
                "Ollama returned no message content "
                f"(model={self.model}, "
                f"done_reason="
                f"{body.get('done_reason', 'unknown')}, "
                f"prompt_tokens="
                f"{body.get('prompt_eval_count', 'unknown')}, "
                f"output_tokens="
                f"{body.get('eval_count', 'unknown')}, "
                f"thinking_chars="
                f"{len(thinking)})"
            )

        try:

            return schema.model_validate_json(
                content
            )

        except ValidationError as exc:

            errors = []

            for error in exc.errors():

                location = ".".join(
                    str(part)
                    for part in error.get(
                        "loc",
                        (),
                    )
                )

                errors.append(
                    (
                        f"type={error.get('type')} "
                        f"loc={location or '<root>'} "
                        f"msg={error.get('msg')}"
                    )
                )

            validation_details = " | ".join(
                errors[:10]
            )

            raise ValueError(
                "Ollama structured response "
                "failed schema validation. "
                f"content_chars={len(content)}; "
                f"done_reason="
                f"{body.get('done_reason', 'unknown')}; "
                f"output_tokens="
                f"{body.get('eval_count', 'unknown')}; "
                f"errors=[{validation_details}]; "
                f"Response preview: "
                f"{content[:1200]}"
            ) from exc
