from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from tqdm import tqdm


INPUT_PATH = Path("data/processed/chunks.jsonl")
OUTPUT_PATH = Path("data/processed/chunks_with_embeddings.jsonl")

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100  # number of chunk texts per API call


def load_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def save_chunks(path: Path, chunks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def batch_iter(items: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Export it in your terminal before running this script."
        )


def main() -> None:
    ensure_api_key()
    client = OpenAI()

    chunks = load_chunks(INPUT_PATH)
    print(f"Loaded {len(chunks)} chunks from {INPUT_PATH}")

    batches = batch_iter(chunks, BATCH_SIZE)
    output_chunks: list[dict[str, Any]] = []

    for batch in tqdm(batches, desc="Embedding batches"):
        texts = [chunk["chunk_text"] for chunk in batch]

        # Retry loop for temporary failures
        for attempt in range(3):
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts,
                )
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"Batch failed (attempt {attempt + 1}/3). Retrying in 2s. Error: {e}")
                time.sleep(2)

        # The API returns embeddings in the same order as the inputs
        embeddings = [item.embedding for item in response.data]

        for chunk, embedding in zip(batch, embeddings):
            chunk_with_embedding = {
                **chunk,
                "embedding_model": EMBEDDING_MODEL,
                "embedding": embedding,
            }
            output_chunks.append(chunk_with_embedding)

    save_chunks(OUTPUT_PATH, output_chunks)
    print(f"Saved {len(output_chunks)} embedded chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()