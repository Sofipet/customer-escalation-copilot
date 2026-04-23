from __future__ import annotations

import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from copilot.chunking import build_chunked_documents
from copilot.utils import load_markdown_documents

PERSIST_DIRECTORY = Path("data/artifacts/chroma_db_structured_v2")
COLLECTION_NAME = "customer_escalation_copilot_structured_v2"


def main() -> None:
    docs = load_markdown_documents()
    print(f"Loaded {len(docs)} markdown documents.")

    chunked_docs = build_chunked_documents(
        docs,
        target_words=180,
        overlap_words=30,
    )
    print(f"Created {len(chunked_docs)} chunked documents.")

    if PERSIST_DIRECTORY.exists():
        shutil.rmtree(PERSIST_DIRECTORY)
        print(f"Removed existing structured index at {PERSIST_DIRECTORY}")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIRECTORY),
    )

    print(f"Saved Chroma collection to {PERSIST_DIRECTORY}")
    print(f"Stored chunks: {vectorstore._collection.count()}")


if __name__ == "__main__":
    main()