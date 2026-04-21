from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field


EMBEDDED_CHUNKS_PATH = Path("data/processed/chunks_with_embeddings.jsonl")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 5


# -----------------------------
# Structured output schema
# -----------------------------
class EvidenceItem(BaseModel):
    chunk_id: str
    file_name: str
    reason: str = Field(description="Why this chunk supports the answer.")


class GroundedEscalationAnswer(BaseModel):
    likely_issue: str
    recommended_next_step: str
    evidence: list[EvidenceItem]
    conflict_warning: str
    insufficient_evidence: bool


# -----------------------------
# Helpers
# -----------------------------
def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Export it in your terminal before running this script."
        )


def load_embedded_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Embedded chunks file not found: {path}\n"
            "Run scripts/build_embeddings.py first."
        )

    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_query(client: OpenAI, query: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return response.data[0].embedding


def retrieve_top_k(
    query: str,
    chunks: list[dict[str, Any]],
    client: OpenAI,
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    query_embedding = embed_query(client, query)

    scored_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored_chunks.append(
            {
                **chunk,
                "score": score,
            }
        )

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


def format_context_for_model(retrieved_chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []

    for i, chunk in enumerate(retrieved_chunks, start=1):
        parts.append(
            f"""[Evidence {i}]
chunk_id: {chunk["chunk_id"]}
file_name: {chunk["file_name"]}
title: {chunk["title"]}
document_type: {chunk["document_type"]}
version: {chunk["version"]}
date: {chunk["date"]}
region: {chunk["region"]}
team: {chunk["team"]}
source_authority: {chunk["source_authority"]}
section_title: {chunk["section_title"]}
retrieval_score: {chunk["score"]:.4f}

chunk_text:
{chunk["chunk_text"]}
"""
        )

    return "\n" + ("\n" + "=" * 80 + "\n").join(parts)


def generate_grounded_answer(
    escalation_text: str,
    retrieved_chunks: list[dict[str, Any]],
    client: OpenAI,
) -> GroundedEscalationAnswer:
    evidence_context = format_context_for_model(retrieved_chunks)

    system_prompt = """
You are a support escalation resolution copilot.

Your task:
- Answer ONLY from the retrieved evidence.
- Do not invent policies, thresholds, release changes, or support actions.
- If the evidence is incomplete or unclear, set insufficient_evidence to true.
- If the evidence appears contradictory, outdated, or inconsistent, explain that in conflict_warning.
- Prefer newer and higher-authority sources when interpreting conflicts.
- Cite only the chunk_id and file_name values that appear in the provided evidence.
- Keep the answer practical and support-oriented.

Return structured output only.
""".strip()

    user_prompt = f"""
Customer escalation:
{escalation_text}

Retrieved evidence:
{evidence_context}

Please produce:
1. likely_issue
2. recommended_next_step
3. evidence
4. conflict_warning
5. insufficient_evidence
""".strip()

    response = client.responses.parse(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text_format=GroundedEscalationAnswer,
    )

    return response.output_parsed


def print_answer(answer: GroundedEscalationAnswer) -> None:
    print("\n" + "=" * 100)
    print("LIKELY ISSUE")
    print("-" * 100)
    print(answer.likely_issue)

    print("\n" + "=" * 100)
    print("RECOMMENDED NEXT STEP")
    print("-" * 100)
    print(answer.recommended_next_step)

    print("\n" + "=" * 100)
    print("EVIDENCE")
    print("-" * 100)
    for item in answer.evidence:
        print(f"- {item.chunk_id} | {item.file_name}")
        print(f"  Reason: {item.reason}")

    print("\n" + "=" * 100)
    print("CONFLICT WARNING")
    print("-" * 100)
    print(answer.conflict_warning)

    print("\n" + "=" * 100)
    print("INSUFFICIENT EVIDENCE")
    print("-" * 100)
    print(answer.insufficient_evidence)


def main() -> None:
    ensure_api_key()
    client = OpenAI()

    chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)
    print(f"Loaded {len(chunks)} embedded chunks.")

    escalation_text = input("\nPaste escalation text:\n> ").strip()
    if not escalation_text:
        raise ValueError("Escalation text cannot be empty.")

    retrieved_chunks = retrieve_top_k(
        query=escalation_text,
        chunks=chunks,
        client=client,
        top_k=TOP_K,
    )

    print("\nTop retrieved chunks:")
    for i, chunk in enumerate(retrieved_chunks, start=1):
        print(
            f"{i}. {chunk['file_name']} | {chunk['section_title']} "
            f"| score={chunk['score']:.4f}"
        )

    answer = generate_grounded_answer(
        escalation_text=escalation_text,
        retrieved_chunks=retrieved_chunks,
        client=client,
    )

    print_answer(answer)


if __name__ == "__main__":
    main()