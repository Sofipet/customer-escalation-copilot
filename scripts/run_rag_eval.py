from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from scripts.test_ranked_grounded_answer import (
    EMBEDDED_CHUNKS_PATH,
    PROMPT_PATH,
    ensure_api_key,
    generate_grounded_answer,
    load_embedded_chunks,
    load_prompt,
    retrieve_top_k,
)


EVAL_CASES_PATH = Path("data/eval/rag_eval_cases.json")
OUTPUT_PATH = Path("data/eval/rag_eval_results.json")


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Eval file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unique_file_names(chunks: list[dict[str, Any]]) -> list[str]:
    seen = set()
    ordered = []
    for chunk in chunks:
        file_name = chunk["file_name"]
        if file_name not in seen:
            seen.add(file_name)
            ordered.append(file_name)
    return ordered


def compute_retrieval_metrics(expected_docs: list[str], retrieved_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    top_docs = unique_file_names(retrieved_chunks)
    top3_docs = top_docs[:3]
    top5_docs = top_docs[:5]

    if not expected_docs:
        return {
            "top_docs": top_docs,
            "hit_at_3": None,
            "hit_at_5": None,
            "doc_coverage": None,
        }

    expected_set = set(expected_docs)
    hit_at_3 = len(expected_set.intersection(top3_docs)) > 0
    hit_at_5 = len(expected_set.intersection(top5_docs)) > 0
    doc_coverage = len(expected_set.intersection(top_docs)) / len(expected_set)

    return {
        "top_docs": top_docs,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "doc_coverage": round(doc_coverage, 3),
    }


def run_eval(with_answers: bool = False) -> dict[str, Any]:
    ensure_api_key()
    client = OpenAI()

    cases = load_eval_cases(EVAL_CASES_PATH)
    chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)
    system_prompt = load_prompt(PROMPT_PATH)

    results = []
    hit3_values = []
    hit5_values = []
    coverage_values = []
    conflict_matches = []
    insufficient_matches = []

    for case in cases:
        question = case["question"]
        expected_docs = case["expected_docs"]

        retrieved_chunks = retrieve_top_k(
            query=question,
            chunks=chunks,
            client=client,
            top_k=5,
        )

        retrieval_metrics = compute_retrieval_metrics(expected_docs, retrieved_chunks)

        if retrieval_metrics["hit_at_3"] is not None:
            hit3_values.append(int(retrieval_metrics["hit_at_3"]))
        if retrieval_metrics["hit_at_5"] is not None:
            hit5_values.append(int(retrieval_metrics["hit_at_5"]))
        if retrieval_metrics["doc_coverage"] is not None:
            coverage_values.append(retrieval_metrics["doc_coverage"])

        result_item = {
            "case_id": case["case_id"],
            "category": case["category"],
            "question": case["question"],
            "expected_docs": expected_docs,
            "expected_should_flag_conflict": case["expected_should_flag_conflict"],
            "expected_insufficient_evidence": case["expected_insufficient_evidence"],
            "expected_answer_summary": case["expected_answer_summary"],
            "retrieval": {
                "top_docs": retrieval_metrics["top_docs"],
                "hit_at_3": retrieval_metrics["hit_at_3"],
                "hit_at_5": retrieval_metrics["hit_at_5"],
                "doc_coverage": retrieval_metrics["doc_coverage"],
            },
        }

        if with_answers:
            answer = generate_grounded_answer(
                escalation_text=question,
                retrieved_chunks=retrieved_chunks,
                client=client,
                system_prompt=system_prompt,
            )

            generated_conflict_flag = bool(answer.conflict_warning.strip())
            generated_insufficient = answer.insufficient_evidence

            conflict_match = generated_conflict_flag == case["expected_should_flag_conflict"]
            insufficient_match = generated_insufficient == case["expected_insufficient_evidence"]

            conflict_matches.append(int(conflict_match))
            insufficient_matches.append(int(insufficient_match))

            result_item["answer_eval"] = {
                "generated_answer": answer.model_dump(),
                "auto_conflict_match": conflict_match,
                "auto_insufficient_match": insufficient_match,
                "manual_groundedness_score": None,
                "manual_citation_quality_score": None,
                "manual_expected_summary_match_score": None,
                "manual_notes": "",
            }

        results.append(result_item)

    summary = {
        "cases_total": len(cases),
        "cases_with_expected_docs": len(hit3_values),
        "retrieval_hit_at_3": round(sum(hit3_values) / len(hit3_values), 3) if hit3_values else None,
        "retrieval_hit_at_5": round(sum(hit5_values) / len(hit5_values), 3) if hit5_values else None,
        "average_doc_coverage": round(sum(coverage_values) / len(coverage_values), 3) if coverage_values else None,
        "answer_conflict_match_rate": round(sum(conflict_matches) / len(conflict_matches), 3) if conflict_matches else None,
        "answer_insufficient_match_rate": round(sum(insufficient_matches) / len(insufficient_matches), 3) if insufficient_matches else None,
        "with_answers": with_answers,
    }

    output = {
        "summary": summary,
        "results": results,
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG evaluation.")
    parser.add_argument(
        "--with-answers",
        action="store_true",
        help="Also generate grounded answers for each eval case (uses more API calls).",
    )
    args = parser.parse_args()

    output = run_eval(with_answers=args.with_answers)

    print("\n=== EVAL SUMMARY ===")
    for key, value in output["summary"].items():
        print(f"{key}: {value}")

    print(f"\nSaved detailed results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()