from __future__ import annotations

from copilot.providers.base import GenerationProvider
from copilot.providers.openai_provider import OpenAIProvider
from copilot.providers.qwen_provider import QwenProvider
from copilot.settings import settings


def get_generation_provider() -> GenerationProvider:
    if settings.generation_provider == "openai":
        return OpenAIProvider()

    if settings.generation_provider == "qwen":
        return QwenProvider()

    raise ValueError(f"Unsupported generation provider: {settings.generation_provider}")