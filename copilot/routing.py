from __future__ import annotations

from copilot.contracts import OwnerType, WarningType


def resolve_owner_and_handoff(
    warning_type: WarningType,
    insufficient_evidence: bool,
    likely_issue: str,
    recommended_next_step: str,
    evidence_file_names: list[str],
) -> tuple[OwnerType, bool, str | None, str]:
    text = f"{likely_issue} {recommended_next_step}".lower()
    files = " ".join(evidence_file_names).lower()

    # If evidence is insufficient and no supported route is present, do not invent handoff
    if insufficient_evidence:
        return (
            OwnerType.UNKNOWN,
            False,
            None,
            "",
        )

    # Strategic-renewal / restricted-override / approval exception cases
    if (
        "strategic renewal" in text
        or "strategic_renewal" in files
        or "policy_strategic_renewal_exceptions" in files
    ):
        return (
            OwnerType.REVENUE_OPERATIONS,
            True,
            None,
            "Strategic renewal approval handling requires Revenue Operations review.",
        )

    # Pricing / threshold interpretation
    if "threshold" in text or "discount" in text:
        return (
            OwnerType.PRICING_OPERATIONS,
            True,
            None,
            "Threshold and pricing-related approval handling requires Pricing Operations review.",
        )

    # Release/workflow / operational routing issues
    if "release" in text or "workflow" in text:
        return (
            OwnerType.PRODUCT_OPERATIONS,
            True,
            None,
            "Workflow and release-related approval behavior requires Product Operations review.",
        )

    # Default support-owned informational case
    return (
        OwnerType.SUPPORT,
        False,
        None,
        "",
    )