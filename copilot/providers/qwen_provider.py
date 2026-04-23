from __future__ import annotations

import json

from openai import OpenAI

from copilot.contracts import EscalationResponse, OwnerType, WarningType
from copilot.providers.base import GenerationProvider
from copilot.settings import settings
from copilot.tracing import traceable


class QwenProvider(GenerationProvider):
    def __init__(self) -> None:
        self.model = settings.qwen_model
        self.client = OpenAI(
            base_url=settings.qwen_base_url,
            api_key=settings.qwen_api_key,
        )

    @traceable(name="qwen_generate_structured_response", run_type="llm")
    def generate_structured_response(self, question: str, context: str) -> EscalationResponse:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": settings.system_prompt},
                {
                    "role": "user",
                    "content": f"Customer escalation:\n{question}\n\nRetrieved context:\n{context}",
                },
            ],
            temperature=0,
        )

        text = completion.choices[0].message.content
        if text is None:
            raise ValueError("Qwen provider returned empty content.")

        text = text.strip()

        if text.startswith("```json"):
            text = text.removeprefix("```json").strip()
        if text.startswith("```"):
            text = text.removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        raw = json.loads(text)

        likely_issue = (
            raw.get("likely_issue")
            or raw.get("most_likely_issue")
            or raw.get("issue")
            or raw.get("problem")
            or "Model did not provide a specific likely issue."
        )

        recommended_next_step = (
            raw.get("recommended_next_step")
            or raw.get("next_practical_action")
            or raw.get("next_step")
            or raw.get("recommended_action")
            or "Escalate for manual review based on the retrieved evidence."
        )

        normalized = {
            "likely_issue": likely_issue,
            "recommended_next_step": recommended_next_step,
            "recommended_owner": raw.get("recommended_owner", "Unknown"),
            "recommended_queue": raw.get("recommended_queue"),
            "requires_human_handoff": raw.get("requires_human_handoff", False),
            "handoff_reason": raw.get("handoff_reason", ""),
            "evidence_ids": raw.get("evidence_ids", []),
            "warning_type": raw.get("warning_type", "none"),
            "warning_message": raw.get("warning_message", ""),
            "insufficient_evidence": raw.get("insufficient_evidence", False),
        }

        valid_owners = {item.value for item in OwnerType}
        if normalized["recommended_owner"] not in valid_owners:
            normalized["recommended_owner"] = "Unknown"

        valid_warning_types = {item.value for item in WarningType}
        if normalized["warning_type"] not in valid_warning_types:
            normalized["warning_type"] = "none"

        if not isinstance(normalized["evidence_ids"], list):
            normalized["evidence_ids"] = []

        return EscalationResponse.model_validate(normalized)