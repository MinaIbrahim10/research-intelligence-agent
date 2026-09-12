from app.config import Settings
from app.providers.base import StructuredLLM
from app.providers.ollama import OllamaStructuredLLM
from app.providers.openai_compatible import OpenAICompatibleStructuredLLM


def build_llm(settings: Settings) -> StructuredLLM:
    if settings.llm_provider == "ollama":
        return OllamaStructuredLLM(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleStructuredLLM(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
