from __future__ import annotations

from copilot.retrieval import retrieve_and_rerank


def main() -> None:
    query = input("Enter retrieval query:\n> ").strip()
    if not query:
        raise ValueError("Query cannot be empty.")

    results = retrieve_and_rerank(query=query, initial_k=10, final_k=8)

    print("\nReranked retrieval results:\n")
    for i, item in enumerate(results, start=1):
        doc = item["doc"]
        meta = doc.metadata

        print("=" * 100)
        print(f"Final rank: {i}")
        print(f"Original dense rank: {item['base_rank']}")
        print(f"Final score: {item['final_score']:.4f}")
        print(f"chunk_id: {meta.get('chunk_id')}")
        print(f"file_name: {meta.get('file_name')}")
        print(f"title: {meta.get('title')}")
        print(f"document_type: {meta.get('document_type')}")
        print(f"version: {meta.get('version')}")
        print(f"date: {meta.get('date')}")
        print(f"region: {meta.get('region')}")
        print(f"source_authority: {meta.get('source_authority')}")
        print(f"section_title: {meta.get('section_title')}")
        print("-" * 100)
        print(doc.page_content[:1200])


if __name__ == "__main__":
    main()