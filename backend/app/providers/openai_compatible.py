import json

import httpx

from app.providers.base import T


class OpenAICompatibleStructuredLLM:
    """Works with servers exposing an OpenAI-compatible /v1/chat/completions endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
    ) -> T:
        json_schema = schema.model_json_schema()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\nReturn JSON matching this schema exactly:\n"
                        f"{json.dumps(json_schema, ensure_ascii=False)}"
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": json_schema,
                },
            },
        }

        endpoint = f"{self.base_url}/v1/chat/completions"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()

        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenAI-compatible endpoint returned an unexpected response") from exc

        return schema.model_validate_json(content)
