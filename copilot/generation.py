from __future__ import annotations

from copilot.contracts import EscalationResponse
from copilot.providers import get_generation_provider
from copilot.routing import resolve_owner_and_handoff
from copilot.tracing import traceable
from copilot.warnings import override_warning_type


def format_docs_for_generation(docs) -> str:
    formatted = []

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        formatted.append(
            f"""[Document {i}]
chunk_id: {meta.get('chunk_id')}
title: {meta.get('title')}
file_name: {meta.get('file_name')}
document_type: {meta.get('document_type')}
version: {meta.get('version')}
date: {meta.get('date')}
region: {meta.get('region')}
source_authority: {meta.get('source_authority')}
section_title: {meta.get('section_title')}

content:
{doc.page_content}
"""
        )

    return "\n\n" + ("-" * 80 + "\n\n").join(formatted)


@traceable(name="generate_structured_response", run_type="chain")
def generate_structured_response(question: str, docs) -> EscalationResponse:
    context = format_docs_for_generation(docs)
    provider = get_generation_provider()
    parsed = provider.generate_structured_response(question=question, context=context)

    evidence_map = {
        doc.metadata.get("chunk_id"): doc.metadata.get("file_name")
        for doc in docs
    }
    evidence_file_names = [
        evidence_map[eid] for eid in parsed.evidence_ids if eid in evidence_map
    ]

    final_warning_type = override_warning_type(
        model_warning_type=parsed.warning_type,
        question=question,
        evidence_file_names=evidence_file_names,
        insufficient_evidence=parsed.insufficient_evidence,
    )

    final_insufficient_evidence = (
        parsed.insufficient_evidence
        or final_warning_type.value == "insufficient_detail"
    )

    owner, requires_handoff, queue, handoff_reason = resolve_owner_and_handoff(
        warning_type=final_warning_type,
        insufficient_evidence=final_insufficient_evidence,
        likely_issue=parsed.likely_issue,
        recommended_next_step=parsed.recommended_next_step,
        evidence_file_names=evidence_file_names,
    )

    return EscalationResponse(
        likely_issue=parsed.likely_issue,
        recommended_next_step=parsed.recommended_next_step,
        recommended_owner=owner,
        recommended_queue=queue,
        requires_human_handoff=requires_handoff,
        handoff_reason=handoff_reason,
        evidence_ids=parsed.evidence_ids,
        warning_type=final_warning_type,
        warning_message=parsed.warning_message,
        insufficient_evidence=final_insufficient_evidence,
    )