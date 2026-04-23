# Customer Escalation Resolution Copilot — V2 Product Contract

## Goal
Given a customer support escalation, retrieve relevant internal guidance and return a structured, policy-grounded recommendation for the next action.

## Primary user
Support engineer / support operations / revenue operations triage

## Input
A single escalation text in natural language.

## Output
The system returns one JSON object with these fields:

- likely_issue: string
- recommended_next_step: string
- recommended_owner: one of [Support, Revenue Operations, Pricing Operations, Product Operations, Unknown]
- recommended_queue: string | null
- requires_human_handoff: boolean
- handoff_reason: string
- evidence_ids: list[string]
- warning_type: one of [none, stale_guidance, conflict, insufficient_detail]
- warning_message: string
- insufficient_evidence: boolean

## Field rules

### likely_issue
Concise diagnosis of the most likely cause of the escalation.

### recommended_next_step
Concrete operational next action.

### recommended_owner
Allowed values only:
- Support
- Revenue Operations
- Pricing Operations
- Product Operations
- Unknown

### recommended_queue
Use only when supported by evidence. Otherwise null.

### requires_human_handoff
True only when escalation or specialist handling is required.

### handoff_reason
Reason for handoff. Empty string allowed when no handoff is needed.

### evidence_ids
Chunk IDs only. No file names or titles.

### warning_type
- none: no meaningful warning
- stale_guidance: older guidance exists but is superseded
- conflict: materially conflicting guidance exists
- insufficient_detail: evidence is not specific enough for a confident answer

### warning_message
Short human-readable warning explanation. Empty string allowed when warning_type is none.

### insufficient_evidence
True when the answer should not be treated as sufficiently supported for confident action.

## Guardrails
- Use only retrieved evidence.
- Prefer newer guidance over older guidance.
- Prefer higher-authority guidance over lower-authority guidance.
- Prefer policy and release notes over informal notes when they disagree.
- Do not invent thresholds, policies, release changes, owners, queues, or metadata.
- Do not cite evidence IDs not present in retrieved context.

## Non-goals
- No write actions
- No ticket updates
- No email sending
- No CRM mutations
- No unauthenticated public endpoint