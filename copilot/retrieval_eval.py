from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from copilot.retrieval import retrieve_and_rerank

EVAL_CASES_PATH = Path("data/eval/v2_eval_cases.json")
OUTPUT_PATH = Path("data/eval/v2_retrieval_eval_results.json")


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Eval file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unique_file_names(results) -> list[str]:
    seen = set()
    ordered = []

    for item in results:
        file_name = item["doc"].metadata.get("file_name")
        if file_name and file_name not in seen:
            seen.add(file_name)
            ordered.append(file_name)

    return ordered


def compute_doc_metrics(target_docs: list[str], top_docs: list[str]) -> dict[str, Any]:
    if not target_docs:
        return {
            "hit_at_3": None,
            "hit_at_5": None,
            "doc_coverage": None,
        }

    target_set = set(target_docs)
    top3_docs = top_docs[:3]
    top5_docs = top_docs[:5]

    hit_at_3 = len(target_set.intersection(top3_docs)) > 0
    hit_at_5 = len(target_set.intersection(top5_docs)) > 0
    doc_coverage = len(target_set.intersection(top_docs)) / len(target_set)

    return {
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "doc_coverage": round(doc_coverage, 3),
    }


def main() -> None:
    cases = load_eval_cases(EVAL_CASES_PATH)

    results = []

    required_hit3_values = []
    required_hit5_values = []
    required_coverage_values = []

    supporting_hit5_values = []
    supporting_coverage_values = []

    for case in cases:
        reranked_results = retrieve_and_rerank(
            query=case["question"],
            initial_k=10,
            final_k=5,
        )

        top_docs = unique_file_names(reranked_results)

        required_docs = case.get("required_docs", [])
        supporting_docs = case.get("supporting_docs", [])

        required_metrics = compute_doc_metrics(required_docs, top_docs)
        supporting_metrics = compute_doc_metrics(supporting_docs, top_docs)

        if required_metrics["hit_at_3"] is not None:
            required_hit3_values.append(int(required_metrics["hit_at_3"]))
        if required_metrics["hit_at_5"] is not None:
            required_hit5_values.append(int(required_metrics["hit_at_5"]))
        if required_metrics["doc_coverage"] is not None:
            required_coverage_values.append(required_metrics["doc_coverage"])

        if supporting_metrics["hit_at_5"] is not None:
            supporting_hit5_values.append(int(supporting_metrics["hit_at_5"]))
        if supporting_metrics["doc_coverage"] is not None:
            supporting_coverage_values.append(supporting_metrics["doc_coverage"])

        results.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "question": case["question"],
                "required_docs": required_docs,
                "supporting_docs": supporting_docs,
                "retrieval": {
                    "top_docs": top_docs,
                    "required_hit_at_3": required_metrics["hit_at_3"],
                    "required_hit_at_5": required_metrics["hit_at_5"],
                    "required_doc_coverage": required_metrics["doc_coverage"],
                    "supporting_hit_at_5": supporting_metrics["hit_at_5"],
                    "supporting_doc_coverage": supporting_metrics["doc_coverage"],
                },
            }
        )

    summary = {
        "cases_total": len(cases),
        "cases_with_required_docs": len(required_hit3_values),
        "required_hit_at_3": round(sum(required_hit3_values) / len(required_hit3_values), 3) if required_hit3_values else None,
        "required_hit_at_5": round(sum(required_hit5_values) / len(required_hit5_values), 3) if required_hit5_values else None,
        "average_required_doc_coverage": round(sum(required_coverage_values) / len(required_coverage_values), 3) if required_coverage_values else None,
        "cases_with_supporting_docs": len(supporting_hit5_values),
        "supporting_hit_at_5": round(sum(supporting_hit5_values) / len(supporting_hit5_values), 3) if supporting_hit5_values else None,
        "average_supporting_doc_coverage": round(sum(supporting_coverage_values) / len(supporting_coverage_values), 3) if supporting_coverage_values else None,
    }

    output = {
        "summary": summary,
        "results": results,
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RETRIEVAL EVAL SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print(f"\nSaved detailed results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()