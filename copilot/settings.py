from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "customer-escalation-copilot")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")

    generation_provider: str = os.getenv("GENERATION_PROVIDER", "openai")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    retrieval_initial_k: int = int(os.getenv("RETRIEVAL_INITIAL_K", "10"))
    retrieval_final_k: int = int(os.getenv("RETRIEVAL_FINAL_K", "5"))

    langsmith_project: str = os.getenv(
        "LANGSMITH_PROJECT",
        "customer-escalation-copilot-v2-dev",
    )

    prompt_path: str = os.getenv(
        "PROMPT_PATH",
        "copilot/prompts/system_prompt.txt",
    )

    demo_access_token: str = os.getenv("DEMO_ACCESS_TOKEN", "demo-access-token")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-to-a-long-random-secret")
    max_live_questions: int = int(os.getenv("MAX_LIVE_QUESTIONS", "3"))

    @property
    def system_prompt(self) -> str:
        return Path(self.prompt_path).read_text(encoding="utf-8").strip()


settings = Settings()