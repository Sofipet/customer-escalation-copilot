from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Customer Escalation Resolution Copilot",
    page_icon="🧭",
    layout="wide",
)

DEMO_OUTPUTS_PATH = Path("data/demo/demo_outputs.json")
DEMO_CASES_PATH = Path("data/demo/demo_cases.json")


@st.cache_data
def load_demo_outputs() -> list[dict]:
    if not DEMO_OUTPUTS_PATH.exists():
        st.error(f"Missing file: {DEMO_OUTPUTS_PATH}")
        return []
    return json.loads(DEMO_OUTPUTS_PATH.read_text(encoding="utf-8"))


@st.cache_data
def load_demo_cases() -> list[dict]:
    if not DEMO_CASES_PATH.exists():
        return []
    return json.loads(DEMO_CASES_PATH.read_text(encoding="utf-8"))


def render_header() -> None:
    st.title("Customer Escalation Resolution Copilot")
    st.caption(
        "Demo mode only — this public version uses precomputed retrieval and answer outputs. "
        "No live API calls are made."
    )

    st.markdown(
        """
This project demonstrates a **retrieval-augmented support copilot** for handling customer escalations.
It helps support teams:
- identify the likely issue,
- recommend the next step,
- cite supporting evidence,
- surface stale or conflicting guidance.
"""
    )


def render_project_overview(outputs: list[dict]) -> None:
    st.subheader("Project overview")

    total_cases = len(outputs)
    total_retrieved_chunks = sum(len(item.get("retrieved_chunks", [])) for item in outputs)

    col1, col2, col3 = st.columns(3)
    col1.metric("Demo cases", total_cases)
    col2.metric("Retrieved chunks shown", total_retrieved_chunks)
    col3.metric("Live API calls", "0")

    with st.expander("What this app is showing", expanded=False):
        st.markdown(
            """
This demo shows the **public showcase version** of the project.

It displays:
- saved escalation examples,
- saved retrieval results,
- saved grounded answers,
- saved evidence and conflict warnings.

The full local development version can use embeddings and model calls, but this deployed version is intentionally
API-free to avoid any usage costs.
"""
        )


def render_case_selector(outputs: list[dict]) -> dict | None:
    st.subheader("Explore a demo case")

    if not outputs:
        st.warning("No demo outputs found.")
        return None

    case_titles = [item["title"] for item in outputs]
    selected_title = st.selectbox("Choose a case", case_titles)

    selected_case = next(item for item in outputs if item["title"] == selected_title)
    return selected_case


def render_answer_section(case: dict) -> None:
    answer = case["answer"]

    st.subheader("Escalation")
    st.code(case["escalation_text"], language=None)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Likely issue")
        st.write(answer["likely_issue"])

        st.subheader("Recommended next step")
        st.write(answer["recommended_next_step"])

    with col2:
        st.subheader("Conflict warning")
        if answer["conflict_warning"].strip():
            st.warning(answer["conflict_warning"])
        else:
            st.success("No major conflict detected in this case.")

        st.subheader("Insufficient evidence")
        if answer["insufficient_evidence"]:
            st.error("True")
        else:
            st.success("False")


def render_evidence_section(case: dict) -> None:
    answer = case["answer"]
    evidence = answer.get("evidence", [])

    st.subheader("Cited evidence")

    if not evidence:
        st.info("No evidence items found.")
        return

    for item in evidence:
        with st.container(border=True):
            st.markdown(f"**Chunk ID:** `{item['chunk_id']}`")
            st.markdown(f"**File:** `{item['file_name']}`")
            st.markdown(f"**Reason:** {item['reason']}")


def render_retrieval_section(case: dict) -> None:
    st.subheader("Top retrieved chunks")

    retrieved_chunks = case.get("retrieved_chunks", [])

    if not retrieved_chunks:
        st.info("No retrieved chunks stored.")
        return

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        title_line = (
            f"{idx}. {chunk['title']} "
            f"({chunk['document_type']}, version {chunk['version']}, authority {chunk['source_authority']})"
        )

        with st.expander(title_line, expanded=(idx == 1)):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**File:** `{chunk['file_name']}`")
            c2.markdown(f"**Section:** {chunk['section_title']}")
            c3.markdown(f"**Final score:** {chunk['final_score']:.4f}")

            st.markdown(f"**Chunk ID:** `{chunk['chunk_id']}`")
            st.markdown("**Chunk text:**")
            st.write(chunk["chunk_text"])


def render_sidebar(outputs: list[dict], cases: list[dict]) -> None:
    st.sidebar.header("About this demo")
    st.sidebar.write(
        "This is a static showcase of the Customer Escalation Resolution Copilot. "
        "It uses precomputed outputs instead of live model calls."
    )

    st.sidebar.header("Data")
    st.sidebar.write(f"Demo output records: {len(outputs)}")
    st.sidebar.write(f"Demo case definitions: {len(cases)}")

    st.sidebar.header("Project scope")
    st.sidebar.markdown(
        """
- domain: quote approval / policy / release-related escalations  
- retrieval-aware support assistance  
- conflict / stale guidance surfacing  
- grounded answers with evidence
"""
    )


def main() -> None:
    outputs = load_demo_outputs()
    cases = load_demo_cases()

    render_sidebar(outputs, cases)
    render_header()
    render_project_overview(outputs)

    selected_case = render_case_selector(outputs)
    if not selected_case:
        return

    tab1, tab2, tab3 = st.tabs(["Resolution", "Evidence", "Retrieved chunks"])

    with tab1:
        render_answer_section(selected_case)

    with tab2:
        render_evidence_section(selected_case)

    with tab3:
        render_retrieval_section(selected_case)


if __name__ == "__main__":
    main()