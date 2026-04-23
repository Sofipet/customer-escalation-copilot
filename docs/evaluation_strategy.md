# V2 Evaluation Strategy

## Goal
Evaluate the copilot as a decision-support system.

## Evaluation layers

### 1. Retrieval
Purpose: verify that retrieval surfaces the core evidence.

Primary metrics:
- required_hit_at_3
- required_hit_at_5
- average_required_doc_coverage

Secondary metrics:
- supporting_hit_at_5
- average_supporting_doc_coverage

Primary thresholds:
- required_hit_at_3 >= 0.85
- required_hit_at_5 >= 0.95
- average_required_doc_coverage >= 0.70

Secondary threshold:
- average_supporting_doc_coverage >= 0.45

### 2. Structured output
Purpose: verify that responses are machine-usable.

Checks:
- schema_valid = 100%
- all required fields present = 100%
- valid warning_type = 100%
- evidence_ids subset of retrieved chunk IDs = 100%

### 3. Product behavior
Purpose: verify operational correctness.

Auto-check fields:
- expected_warning_type
- expected_insufficient_evidence
- expected_owner
- expected_requires_human_handoff

Thresholds:
- warning_type_accuracy >= 0.85
- insufficient_evidence_accuracy >= 0.95
- owner_accuracy >= 0.80
- requires_human_handoff_accuracy >= 0.85

### 4. Manual review
Purpose: verify groundedness and usefulness.

Review fields:
- groundedness_score
- actionability_score
- warning_quality_score
- owner_rationale_score
- manual_notes

Scale:
- 1.0 = correct / strong
- 0.5 = partly correct
- 0.0 = incorrect / weak

Sample thresholds:
- average_groundedness_score >= 0.85
- average_actionability_score >= 0.80
- average_warning_quality_score >= 0.80

## Release gates
Reject a candidate version if:
- schema_valid < 100%
- evidence_ids contain IDs outside retrieved context
- warning_type_accuracy is below threshold
- insufficient_evidence_accuracy is below threshold
- required_hit_at_5 is below threshold
- critical unsupported policy or routing claims appear in manual review

## Change policy
Before any major change, record:
- retrieval metrics
- structured output checks
- behavior metrics

After the change, rerun the same eval set and compare.

Major changes include:
- chunking
- embedding model
- retrieval/reranking
- prompt
- generation model
- schema
- hybrid business logic

Accept a change only if:
- quality improves, or
- quality remains acceptable while another tradeoff improves

## Optional tracking
When useful, also track:
- retrieval latency
- generation latency
- total latency
- model name
- approximate tokens
- approximate cost

## Manual review policy
Manual review is required for:
- new prompt versions
- new generation models
- warning logic changes
- routing logic changes
- release candidates