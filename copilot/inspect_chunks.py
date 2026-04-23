from __future__ import annotations

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

PERSIST_DIRECTORY = "data/artifacts/chroma_db_structured_v2"
COLLECTION_NAME = "customer_escalation_copilot_structured_v2"


def main() -> None:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )

    results = vectorstore._collection.get(include=["documents", "metadatas"])

    documents = results["documents"]
    metadatas = results["metadatas"]

    for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        print("=" * 100)
        print(f"Chunk {i}")
        print(f"chunk_id: {meta.get('chunk_id')}")
        print(f"file_name: {meta.get('file_name')}")
        print(f"title: {meta.get('title')}")
        print(f"document_type: {meta.get('document_type')}")
        print(f"version: {meta.get('version')}")
        print(f"section_title: {meta.get('section_title')}")
        print(f"word_count: {meta.get('word_count')}")
        print("-" * 100)
        print(doc[:1200])

        if i >= 12:
            break


if __name__ == "__main__":
    main()