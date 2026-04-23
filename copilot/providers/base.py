from __future__ import annotations

from abc import ABC, abstractmethod

from copilot.contracts import EscalationResponse


class GenerationProvider(ABC):
    @abstractmethod
    def generate_structured_response(self, question: str, context: str) -> EscalationResponse:
        raise NotImplementedError