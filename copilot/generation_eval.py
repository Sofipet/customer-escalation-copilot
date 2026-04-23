from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from copilot.generation import generate_structured_response
from copilot.retrieval import retrieve_and_rerank

from copilot.tracing import maybe_trace

EVAL_CASES_PATH = Path("data/eval/v2_generation_eval_cases.json")
OUTPUT_PATH = Path("data/eval/v2_generation_eval_results.json")


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Eval file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    cases = load_eval_cases(EVAL_CASES_PATH)

    results = []
    warning_matches = []
    insufficient_matches = []
    owner_matches = []
    handoff_matches = []
    valid_evidence_matches = []

    with maybe_trace(enabled=True, project="customer-escalation-copilot-v2-eval"):
        for case in cases:
            retrieval_results = retrieve_and_rerank(
                query=case["question"],
                initial_k=10,
                final_k=5,
            )
            docs = [item["doc"] for item in retrieval_results]
            retrieved_chunk_ids = {doc.metadata.get("chunk_id") for doc in docs}

            response = generate_structured_response(case["question"], docs)
            response_dict = response.model_dump()

            warning_match = response.warning_type.value == case["expected_warning_type"]
            insufficient_match = response.insufficient_evidence == case["expected_insufficient_evidence"]
            owner_match = response.recommended_owner.value == case["expected_owner"]
            handoff_match = response.requires_human_handoff == case["expected_requires_human_handoff"]
            valid_evidence_match = all(eid in retrieved_chunk_ids for eid in response.evidence_ids)

            warning_matches.append(int(warning_match))
            insufficient_matches.append(int(insufficient_match))
            owner_matches.append(int(owner_match))
            handoff_matches.append(int(handoff_match))
            valid_evidence_matches.append(int(valid_evidence_match))

            results.append(
                {
                    "case_id": case["case_id"],
                    "category": case["category"],
                    "question": case["question"],
                    "expected_warning_type": case["expected_warning_type"],
                    "expected_insufficient_evidence": case["expected_insufficient_evidence"],
                    "expected_owner": case["expected_owner"],
                    "expected_requires_human_handoff": case["expected_requires_human_handoff"],
                    "retrieved_chunk_ids": list(retrieved_chunk_ids),
                    "response": response_dict,
                    "auto_eval": {
                        "warning_type_match": warning_match,
                        "insufficient_evidence_match": insufficient_match,
                        "owner_match": owner_match,
                        "requires_human_handoff_match": handoff_match,
                        "valid_evidence_ids": valid_evidence_match,
                        "manual_groundedness_score": None,
                        "manual_actionability_score": None,
                        "manual_warning_quality_score": None,
                        "manual_owner_rationale_score": None,
                        "manual_notes": "",
                    },
                }
            )

    summary = {
        "cases_total": len(cases),
        "warning_type_accuracy": round(sum(warning_matches) / len(warning_matches), 3) if warning_matches else None,
        "insufficient_evidence_accuracy": round(sum(insufficient_matches) / len(insufficient_matches), 3) if insufficient_matches else None,
        "owner_accuracy": round(sum(owner_matches) / len(owner_matches), 3) if owner_matches else None,
        "requires_human_handoff_accuracy": round(sum(handoff_matches) / len(handoff_matches), 3) if handoff_matches else None,
        "valid_evidence_ids_rate": round(sum(valid_evidence_matches) / len(valid_evidence_matches), 3) if valid_evidence_matches else None,
    }

    output = {
        "summary": summary,
        "results": results,
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== GENERATION EVAL SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print(f"\nSaved detailed results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()