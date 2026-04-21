from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from openai import OpenAI


EMBEDDED_CHUNKS_PATH = Path("data/processed/chunks_with_embeddings.jsonl")
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5


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
        model=EMBEDDING_MODEL,
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
                "score": score,
                "chunk_id": chunk["chunk_id"],
                "file_name": chunk["file_name"],
                "title": chunk["title"],
                "document_type": chunk["document_type"],
                "version": chunk["version"],
                "region": chunk["region"],
                "section_title": chunk["section_title"],
                "chunk_text": chunk["chunk_text"],
            }
        )

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


def print_results(results: list[dict[str, Any]]) -> None:
    for i, item in enumerate(results, start=1):
        print("=" * 100)
        print(f"Rank: {i}")
        print(f"Score: {item['score']:.4f}")
        print(f"File: {item['file_name']}")
        print(f"Title: {item['title']}")
        print(f"Type: {item['document_type']} | Version: {item['version']} | Region: {item['region']}")
        print(f"Section: {item['section_title']}")
        print("-" * 100)
        print(item["chunk_text"][:1000])
        print()


def main() -> None:
    ensure_api_key()
    client = OpenAI()

    chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)
    print(f"Loaded {len(chunks)} embedded chunks.\n")

    query = input("Enter your query: ").strip()
    if not query:
        raise ValueError("Query cannot be empty.")

    results = retrieve_top_k(query=query, chunks=chunks, client=client, top_k=TOP_K)
    print_results(results)


if __name__ == "__main__":
    main()