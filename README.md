# Customer Escalation Resolution Copilot

A retrieval-augmented support copilot for resolving quote-approval escalations using internal guidance such as release notes, policy documents, support articles, troubleshooting guides, and incident summaries.

- **V2 Live demo:** [Render App](https://customer-escalation-copilot.onrender.com)
  
- **V1 Prototype:** [Streamlit App](https://customer-escalation-copilot-c4rcuwabge3grajo2y5bqy.streamlit.app/)

## Overview

Support teams often work across fragmented documentation, overlapping guidance, and policy changes introduced across releases. This project demonstrates how a retrieval-augmented generation system can help triage escalations more consistently by retrieving relevant internal evidence, identifying likely causes, surfacing stale or conflicting guidance, and recommending the next operational step in a structured format.

The system is designed as a **decision-support tool**, not an autonomous agent. It does not update tickets or mutate external systems. Its purpose is to help support and operations users reach the correct next action faster and with a clearer evidence trail.

## V1 to V2 evolution

The project began as a simpler **V1 Streamlit prototype** focused on retrieval and basic answer generation. In **V2**, it was redesigned as a more production-realistic decision-support system with a structured response schema, stronger retrieval setup, explicit evaluation, a protected live mode, a custom UI, and Dockerized deployment. The shift from V1 to V2 was not only a UI upgrade, but a move toward a more disciplined product and engineering architecture.

## What the system does

Given a customer escalation, it:

- retrieves the most relevant internal guidance
- reranks the retrieved evidence
- generates a structured recommendation
- identifies the likely issue
- recommends the next practical step
- assigns the likely owner for the next action
- flags stale guidance, conflict, or insufficient detail when relevant
- returns evidence IDs and retrieved chunks for inspection

## Example use case

A support engineer receives an escalation stating that a customer in Germany cannot complete quote approval after release 2409. An older KB article suggests manual override may still be possible, but newer release guidance appears stricter.

The system retrieves policy and release guidance, identifies that the case is a strategic renewal with protected routing, recommends routing to Revenue Operations rather than attempting override, and flags the conflict between older support assumptions and current policy.

## Architecture

### Retrieval layer
- markdown corpus
- metadata-aware chunking
- embedding-based semantic retrieval
- reranking over retrieved candidates
- chunk-level evidence tracking

### Generation layer
- policy-grounded prompting
- structured output schema
- warning and routing postprocessing
- evidence-aware response formatting

### App layer
- FastAPI backend
- custom HTML/CSS/JS interface
- Dockerized deployment
- public demo mode + protected live mode

## Model setup

### Retrieval
- Embedding model (baseline): `text-embedding-3-small`
- Vector store: Chroma

### Generation
- Primary baseline: `gpt-4o-mini`
- Open-source comparison: `Qwen3-0.6B` via local serving


## Tech stack

- Python
- FastAPI
- Docker
- OpenAI API
- LangChain
- Chroma
- Pydantic
- HTML / CSS / JavaScript
- LangSmith

## Evaluation

The system was evaluated as a **decision-support product**, not only as a generative model.

### Retrieval comparison

| Retrieval variant | Hit@3 | Hit@5 | Avg. doc coverage | Notes |
|---|---:|---:|---:|---|
| Initial Chroma index | 1.00 | 1.00 | 0.692 | Strong retrieval, but lower overall coverage |
| Structured v2 index | 1.00 | 1.00 | 0.950 (required docs) | Best current retrieval baseline |

The structured v2 index improved coverage substantially while preserving perfect hit@3 and hit@5 on the curated eval set.

### Generation comparison

| Generation model | Warning accuracy | Insufficient evidence | Owner accuracy | Handoff accuracy | Valid evidence IDs |
|---|---:|---:|---:|---:|---:|
| OpenAI baseline | 0.917 | 1.000 | 0.833 | 0.833 | 1.000 |
| Qwen local comparison | 0.583 | 0.833 | 0.500 | 0.833 | 1.000 |

### Manual review averages (OpenAI baseline)

| Metric | Score |
|---|---:|
| Groundedness | 0.917 |
| Actionability | 0.792 |
| Warning quality | 0.792 |
| Owner rationale | 0.833 |

### Key takeaway

- Retrieval is quite strong, especially with the structured v2 index.
- The OpenAI baseline produced the most reliable structured outputs.
- The Qwen comparison was useful as an engineering experiment, but showed substantially weaker warning behavior, owner prediction, and overall output quality than the main baseline.

## User experience

The app supports two modes:

### Demo mode
Returns a stored example response without making live API calls.

### Live mode
Requires a protection token and supports limited live usage.

The interface shows:
- the final recommendation
- warning status
- owner and handoff decision
- evidence IDs
- retrieved chunks, expandable on demand

## Run locally

```bash
git clone https://github.com/Sofipet/customer-escalation-copilot.git
cd customer-escalation-copilot
pip install -r requirements.txt

export OPENAI_API_KEY="your_openai_api_key"
export GENERATION_PROVIDER="openai"
export APP_ACCESS_TOKEN="your_protection_token"
export LIVE_REQUEST_LIMIT="3"

uvicorn copilot.api:app --reload
```
Open http://127.0.0.1:8000

## Limitations

- a showcase deployment, not a full enterprise production system
- live access protection is intentionally lightweight
- supporting-document coverage is still weaker than required-document coverage
- warning quality can still be improved in edge cases separating stale guidance from true conflict
- the open-source comparison model used here was too weak to replace the main baseline

## Future improvements

- improve retrieval beyond core required documents, especially supporting and edge-case guidance
- sharpen warning logic and recommendation quality in borderline cases, especially for **stale guidance** vs **true conflict**
- expand evaluation with more diverse scenarios, larger manual review, and stronger open-source model comparisons under the same setup
- replace showcase-grade live access protection with more robust server-side access control if the app is shared more broadly
