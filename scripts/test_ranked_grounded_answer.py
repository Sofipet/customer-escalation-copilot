from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field


EMBEDDED_CHUNKS_PATH = Path("data/processed/chunks_with_embeddings.jsonl")
PROMPT_PATH = Path("app/generation/prompt_template.txt")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TOP_K = 5


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


def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Export it in your terminal before running this script."
        )


def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


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


def authority_score(value: str) -> float:
    mapping = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.2,
    }
    return mapping.get(str(value).lower(), 0.0)


def document_type_score(value: str) -> float:
    mapping = {
        "policy": 1.0,
        "release_note": 0.9,
        "support_kb": 0.7,
        "troubleshooting": 0.6,
        "meeting_note": 0.3,
    }
    return mapping.get(str(value).lower(), 0.0)


def recency_score(date_value: str) -> float:
    if not date_value:
        return 0.0
    try:
        doc_date = datetime.strptime(date_value, "%Y-%m-%d")
        reference_date = datetime.strptime("2025-12-31", "%Y-%m-%d")
        diff_days = max((reference_date - doc_date).days, 0)

        if diff_days <= 90:
            return 1.0
        if diff_days <= 180:
            return 0.8
        if diff_days <= 365:
            return 0.5
        return 0.2
    except ValueError:
        return 0.0


def combined_score(chunk: dict[str, Any], query_embedding: list[float]) -> float:
    semantic = cosine_similarity(query_embedding, chunk["embedding"])
    authority = authority_score(chunk.get("source_authority", ""))
    doc_type = document_type_score(chunk.get("document_type", ""))
    recency = recency_score(chunk.get("date", ""))

    # Weighted sum
    return (
        0.65 * semantic
        + 0.15 * authority
        + 0.10 * doc_type
        + 0.10 * recency
    )


def retrieve_top_k(
    query: str,
    chunks: list[dict[str, Any]],
    client: OpenAI,
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    query_embedding = embed_query(client, query)

    scored_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        semantic = cosine_similarity(query_embedding, chunk["embedding"])
        final_score = combined_score(chunk, query_embedding)

        scored_chunks.append(
            {
                **chunk,
                "semantic_score": semantic,
                "final_score": final_score,
            }
        )

    scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
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
semantic_score: {chunk["semantic_score"]:.4f}
final_score: {chunk["final_score"]:.4f}

chunk_text:
{chunk["chunk_text"]}
"""
        )

    return "\n" + ("\n" + "=" * 80 + "\n").join(parts)


def generate_grounded_answer(
    escalation_text: str,
    retrieved_chunks: list[dict[str, Any]],
    client: OpenAI,
    system_prompt: str,
) -> GroundedEscalationAnswer:
    evidence_context = format_context_for_model(retrieved_chunks)

    user_prompt = f"""
Customer escalation:
{escalation_text}

Retrieved evidence:
{evidence_context}
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

    system_prompt = load_prompt(PROMPT_PATH)
    chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)

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
            f"| semantic={chunk['semantic_score']:.4f} "
            f"| final={chunk['final_score']:.4f}"
        )

    answer = generate_grounded_answer(
        escalation_text=escalation_text,
        retrieved_chunks=retrieved_chunks,
        client=client,
        system_prompt=system_prompt,
    )

    print_answer(answer)


if __name__ == "__main__":
    main()