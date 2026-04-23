from __future__ import annotations

from copilot.contracts import WarningType


def override_warning_type(
    model_warning_type: WarningType,
    question: str,
    evidence_file_names: list[str],
    insufficient_evidence: bool,
) -> WarningType:
    q = question.lower()
    files = " ".join(evidence_file_names).lower()

    if insufficient_evidence:
        return WarningType.INSUFFICIENT_DETAIL

    has_2024_policy = "policy_quote_approval_2024" in files
    has_2025_policy = "policy_quote_approval_2025" in files
    has_2409_release = "release_notes_2409_approval_workflow_change" in files

    has_old_guidance_context = (
        "support article says" in q
        or "older guidance" in q
        or "legacy" in q
        or has_2024_policy
    )

    asks_exact = "exact" in q
    asks_threshold_or_route = "threshold" in q or "route" in q
    has_niche_qualifier = (
        "nonprofit" in q
        or "education" in q
        or "canada" in q
        or "university" in q
    )

    # Exact niche subtype questions should remain insufficient unless explicitly supported
    if asks_exact and asks_threshold_or_route and has_niche_qualifier:
        return WarningType.INSUFFICIENT_DETAIL

    # Explicit conflict framing in the user question plus newer guidance present
    if (
        ("support article says" in q or "release notes suggest" in q or "but" in q)
        and has_2409_release
        and has_old_guidance_context
    ):
        return WarningType.CONFLICT

    # Current-guidance question with both old and new policy present
    if (
        ("current" in q or "latest" in q or "current quote approval rules" in q)
        and has_2024_policy
        and has_2025_policy
    ):
        return WarningType.STALE_GUIDANCE

    # Strategic-renewal cases that include both newer release guidance and older approval guidance
    if (
        "strategic renewal" in q
        and has_2409_release
        and has_2024_policy
    ):
        return WarningType.CONFLICT

    return model_warning_type