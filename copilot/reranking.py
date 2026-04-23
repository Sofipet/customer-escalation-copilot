from __future__ import annotations

from datetime import datetime
from typing import Any

from copilot.query_analysis import extract_query_features

REFERENCE_DATE = datetime.strptime("2025-12-31", "%Y-%m-%d")


def authority_score(value: str) -> float:
    mapping = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.2,
    }
    return mapping.get(str(value).lower(), 0.0)


def document_type_score(value: str) -> float:
    mapping = {
        "policy": 1.0,
        "release_note": 0.95,
        "support_kb": 0.60,
        "troubleshooting": 0.55,
        "meeting_note": 0.35,
    }
    return mapping.get(str(value).lower(), 0.0)


def recency_score(date_value: str) -> float:
    if not date_value:
        return 0.0

    try:
        doc_date = datetime.strptime(date_value, "%Y-%m-%d")
        diff_days = max((REFERENCE_DATE - doc_date).days, 0)

        if diff_days <= 90:
            return 1.0
        if diff_days <= 180:
            return 0.8
        if diff_days <= 365:
            return 0.5
        return 0.2
    except ValueError:
        return 0.0


def alignment_score(metadata: dict[str, Any], features: dict[str, Any], page_content: str) -> float:
    score = 0.0

    doc_type = str(metadata.get("document_type", "")).lower()
    region = str(metadata.get("region", "")).lower()
    version = str(metadata.get("version", "")).lower()
    title = str(metadata.get("title", "")).lower()
    section_title = str(metadata.get("section_title", "")).lower()
    content = page_content.lower()

    # Region match
    if features["region"] and region == features["region"]:
        score += 0.8

    # Release/version match
    if features["release_version"] and features["release_version"] in version:
        score += 0.9

    # Strategic-renewal alignment is very important in this domain
    if features["mentions_strategic_renewal"]:
        if "strategic renewal" in title or "strategic renewal" in section_title or "strategic renewal" in content:
            score += 1.4

    # Manual override alignment matters, but should not dominate
    if features["mentions_manual_override"]:
        if "manual override" in title or "manual override" in section_title or "manual override" in content:
            score += 0.4

    # If the query clearly asks for current guidance, favor policy/release sources
    if features["needs_current_guidance"]:
        if doc_type == "policy":
            score += 0.8
        elif doc_type == "release_note":
            score += 0.9
        elif doc_type == "support_kb":
            score -= 0.2

    # If the query asks what support should do next, favor operational guidance
    if features["needs_routing"]:
        if "support guidance" in section_title or "resolution guidance" in section_title:
            score += 0.9
        if "escalat" in content or "route" in content:
            score += 0.5
    
    if features["mentions_strategic_renewal"] and features["needs_routing"]:
        if "exception" in title or "exception" in section_title or "exception" in content:
            score += 0.6

    # If the query implies conflict/staleness, old support KB may still be relevant,
    # but should not outrank current policy/release docs too easily.
    if features["mentions_conflict"]:
        if doc_type in {"policy", "release_note"}:
            score += 0.5
        elif doc_type == "support_kb":
            score += 0.1

    return score


def support_kb_penalty(metadata: dict[str, Any], features: dict[str, Any]) -> float:
    doc_type = str(metadata.get("document_type", "")).lower()

    if doc_type != "support_kb":
        return 0.0

    penalty = 0.0

    # In current-guidance cases, support KB should be less trusted
    if features["needs_current_guidance"]:
        penalty += 0.15

    # In strategic-renewal cases, generic support KB should not dominate
    if features["mentions_strategic_renewal"]:
        penalty += 0.08

    return penalty


def compute_final_score(
    base_rank: int,
    metadata: dict[str, Any],
    page_content: str,
    features: dict[str, Any],
) -> float:
    dense_prior = max(0.0, 1.0 - 0.08 * (base_rank - 1))

    authority = authority_score(metadata.get("source_authority", ""))
    doc_type = document_type_score(metadata.get("document_type", ""))
    recency = recency_score(metadata.get("date", ""))
    alignment = alignment_score(metadata, features, page_content)
    kb_penalty = support_kb_penalty(metadata, features)

    return (
        0.30 * dense_prior
        + 0.20 * authority
        + 0.20 * doc_type
        + 0.15 * recency
        + 0.15 * alignment
        - kb_penalty
    )


def rerank_docs(retrieved_docs, query: str):
    features = extract_query_features(query)

    scored = []
    for rank, doc in enumerate(retrieved_docs, start=1):
        final_score = compute_final_score(
            base_rank=rank,
            metadata=doc.metadata,
            page_content=doc.page_content,
            features=features,
        )

        scored.append(
            {
                "doc": doc,
                "base_rank": rank,
                "final_score": final_score,
                "query_features": features,
            }
        )

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored