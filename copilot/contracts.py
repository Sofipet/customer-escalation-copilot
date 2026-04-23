from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WarningType(str, Enum):
    NONE = "none"
    STALE_GUIDANCE = "stale_guidance"
    CONFLICT = "conflict"
    INSUFFICIENT_DETAIL = "insufficient_detail"


class OwnerType(str, Enum):
    SUPPORT = "Support"
    REVENUE_OPERATIONS = "Revenue Operations"
    PRICING_OPERATIONS = "Pricing Operations"
    PRODUCT_OPERATIONS = "Product Operations"
    UNKNOWN = "Unknown"


class EscalationResponse(BaseModel):
    likely_issue: str = Field(min_length=1)
    recommended_next_step: str = Field(min_length=1)
    recommended_owner: OwnerType
    recommended_queue: Optional[str] = None
    requires_human_handoff: bool
    handoff_reason: str
    evidence_ids: list[str]
    warning_type: WarningType
    warning_message: str
    insufficient_evidence: bool