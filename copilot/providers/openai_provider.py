from __future__ import annotations

from openai import OpenAI

from copilot.contracts import EscalationResponse
from copilot.providers.base import GenerationProvider
from copilot.settings import settings
from copilot.tracing import get_traced_openai_client, traceable


class OpenAIProvider(GenerationProvider):
    def __init__(self) -> None:
        self.model = settings.openai_model
        self.client: OpenAI = get_traced_openai_client()

    @traceable(name="openai_generate_structured_response", run_type="llm")
    def generate_structured_response(self, question: str, context: str) -> EscalationResponse:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": settings.system_prompt},
                {
                    "role": "user",
                    "content": f"Customer escalation:\n{question}\n\nRetrieved context:\n{context}",
                },
            ],
            text_format=EscalationResponse,
        )
        return response.output_parsed