from __future__ import annotations

import os
from functools import lru_cache

import openai
from langsmith import Client, traceable, tracing_context
from langsmith.wrappers import wrap_openai


@lru_cache(maxsize=1)
def get_langsmith_client() -> Client:
    return Client(
        api_key=os.getenv("LANGSMITH_API_KEY"),
        workspace_id=os.getenv("LANGSMITH_WORKSPACE_ID"),
    )


@lru_cache(maxsize=1)
def get_traced_openai_client():
    return wrap_openai(openai.OpenAI())


def maybe_trace(enabled: bool = True, project: str | None = None):
    if not enabled:
        return tracing_context(enabled=False)

    client = get_langsmith_client()
    return tracing_context(
        enabled=True,
        client=client,
        project_name=project,
    )