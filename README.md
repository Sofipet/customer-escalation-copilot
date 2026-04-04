# Customer Escalation Resolution Copilot

A retrieval-augmented AI copilot for resolving customer support escalations using internal knowledge such as release notes, support articles, policy documents, troubleshooting guides, and incident notes.

**Live demo:** [Streamlit App](https://sofipet-customer-escalation-copilot-streamlit-app-zfw5oy.streamlit.app/)  

## Overview

Support teams often work with fragmented and sometimes outdated documentation. This project demonstrates how a RAG-based system can help resolve escalations faster by retrieving the most relevant internal guidance, surfacing conflicting information, and generating grounded, evidence-based support recommendations.

The current public app is deployed in **demo mode** and uses **precomputed retrieval and answer outputs**. It does **not** make live API calls.

## What the system does

Given a customer escalation, the system:

- retrieves the most relevant internal documents
- identifies the likely issue
- recommends the next support step
- cites supporting evidence
- flags potentially stale or conflicting guidance

## Example use case

A support engineer investigates a case where a customer in Germany cannot complete quote approval after a product update.  
The system compares release notes, policy documents, and support KB articles to explain the likely reason, recommend the next action, and highlight if older support guidance is no longer reliable.

## Key features

- Markdown-based document ingestion
- Metadata-aware chunking
- Semantic retrieval with embeddings
- Grounded answer generation with cited evidence
- Conflict / stale-guidance warning
- Safe public demo mode with no live API usage

## Tech stack

- Python
- OpenAI API
- Streamlit
- JSON / Markdown document corpus
  
