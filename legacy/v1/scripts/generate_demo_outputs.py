from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from test_ranked_grounded_answer import (
    EMBEDDED_CHUNKS_PATH,
    PROMPT_PATH,
    generate_grounded_answer,
    load_embedded_chunks,
    load_prompt,
    retrieve_top_k,
    ensure_api_key,
)


DEMO_CASES_PATH = Path("data/demo/demo_cases.json")
DEMO_OUTPUTS_PATH = Path("data/demo/demo_outputs.json")


def main() -> None:
    ensure_api_key()
    client = OpenAI()

    system_prompt = load_prompt(PROMPT_PATH)
    chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)

    cases = json.loads(DEMO_CASES_PATH.read_text(encoding="utf-8"))
    outputs: list[dict[str, Any]] = []

    for case in cases:
        escalation_text = case["escalation_text"]

        retrieved_chunks = retrieve_top_k(
            query=escalation_text,
            chunks=chunks,
            client=client,
            top_k=5,
        )

        answer = generate_grounded_answer(
            escalation_text=escalation_text,
            retrieved_chunks=retrieved_chunks,
            client=client,
            system_prompt=system_prompt,
        )

        outputs.append(
            {
                "case_id": case["case_id"],
                "title": case["title"],
                "escalation_text": escalation_text,
                "retrieved_chunks": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "file_name": chunk["file_name"],
                        "title": chunk["title"],
                        "section_title": chunk["section_title"],
                        "document_type": chunk["document_type"],
                        "version": chunk["version"],
                        "source_authority": chunk["source_authority"],
                        "semantic_score": chunk["semantic_score"],
                        "final_score": chunk["final_score"],
                        "chunk_text": chunk["chunk_text"],
                    }
                    for chunk in retrieved_chunks
                ],
                "answer": answer.model_dump(),
            }
        )

    DEMO_OUTPUTS_PATH.write_text(
        json.dumps(outputs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved demo outputs to {DEMO_OUTPUTS_PATH}")


if __name__ == "__main__":
    main()