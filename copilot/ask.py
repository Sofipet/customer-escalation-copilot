from __future__ import annotations

import json

from copilot.generation import generate_structured_response
from copilot.retrieval import retrieve_and_rerank

from copilot.tracing import maybe_trace


def main() -> None:
    question = input("Ask a question / paste an escalation:\n> ").strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    with maybe_trace(enabled=True, project="customer-escalation-copilot-v2-dev"):
        results = retrieve_and_rerank(question, initial_k=10, final_k=5)
        final_docs = [item["doc"] for item in results]

        print("\nTop reranked chunks:")
        for i, item in enumerate(results, start=1):
            doc = item["doc"]
            meta = doc.metadata
            print(
                f"{i}. {meta.get('chunk_id')} | {meta.get('file_name')} | "
                f"{meta.get('section_title')} | score={item['final_score']:.4f}"
            )

        structured_response = generate_structured_response(question, final_docs)

        print("\n" + "=" * 100)
        print(json.dumps(structured_response.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()