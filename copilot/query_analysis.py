from __future__ import annotations

import re
from typing import Any


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_query_features(query: str) -> dict[str, Any]:
    q = normalize_text(query)

    region = None
    if "germany" in q:
        region = "germany"
    elif "eu" in q or "europe" in q:
        region = "eu"
    elif "canada" in q:
        region = "canada"

    release_version = None
    version_match = re.search(r"\b(24\d{2}|25\d{2})\b", q)
    if version_match:
        release_version = version_match.group(1)

    return {
        "region": region,
        "release_version": release_version,
        "mentions_manual_override": "manual override" in q,
        "mentions_strategic_renewal": "strategic renewal" in q or "strategic renewals" in q,
        "needs_current_guidance": any(
            phrase in q
            for phrase in [
                "current",
                "latest",
                "updated",
                "after",
                "now",
                "workflow changed",
                "release changed",
            ]
        ),
        "needs_routing": any(
            phrase in q
            for phrase in [
                "what should support do next",
                "what should support do",
                "who should handle",
                "route",
                "escalate",
                "next step",
            ]
        ),
        "needs_policy": any(
            phrase in q
            for phrase in [
                "policy",
                "rule",
                "allowed",
                "approval threshold",
                "guidance",
            ]
        ),
        "mentions_conflict": any(
            phrase in q
            for phrase in [
                "conflict",
                "contradict",
                "support article says",
                "release notes suggest",
                "but",
                "however",
            ]
        ),
    }