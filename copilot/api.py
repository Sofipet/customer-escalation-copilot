from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from copilot.generation import generate_structured_response
from copilot.retrieval import retrieve_and_rerank
from copilot.settings import settings

app = FastAPI(
    title="Customer Escalation Resolution Copilot API",
    version=settings.app_version,
    description="Policy-grounded support escalation resolver for quote approval cases.",
)

WEB_DIR = Path("copilot/web")
DEMO_RESPONSE_PATH = Path("data/demo/demo_outputs.json")

APP_ACCESS_TOKEN = os.getenv("APP_ACCESS_TOKEN", "demo-token")
LIVE_REQUEST_LIMIT = int(os.getenv("LIVE_REQUEST_LIMIT", "3"))

# simple in-memory tracking for showcase mode
live_usage_by_token: dict[str, int] = {}


class ResolveRequest(BaseModel):
    escalation_text: str = Field(min_length=1, description="Customer escalation text")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of final retrieved chunks")


class RetrievedChunk(BaseModel):
    chunk_id: Optional[str]
    file_name: Optional[str]
    title: Optional[str]
    section_title: Optional[str]
    document_type: Optional[str]
    version: Optional[str]
    final_score: float
    content: Optional[str] = None


class ResolveResponse(BaseModel):
    mode: str
    escalation_text: str
    likely_issue: str
    recommended_next_step: str
    recommended_owner: str
    recommended_queue: Optional[str]
    requires_human_handoff: bool
    handoff_reason: str
    evidence_ids: list[str]
    warning_type: str
    warning_message: str
    insufficient_evidence: bool
    retrieved_chunks: list[RetrievedChunk]


def build_live_response(payload: ResolveRequest) -> ResolveResponse:
    results = retrieve_and_rerank(
        query=payload.escalation_text,
        initial_k=settings.retrieval_initial_k,
        final_k=payload.top_k,
    )

    docs = [item["doc"] for item in results]
    response = generate_structured_response(payload.escalation_text, docs)

    retrieved_chunks = []
    for item in results:
        doc = item["doc"]
        meta = doc.metadata
        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=meta.get("chunk_id"),
                file_name=meta.get("file_name"),
                title=meta.get("title"),
                section_title=meta.get("section_title"),
                document_type=meta.get("document_type"),
                version=str(meta.get("version")) if meta.get("version") is not None else None,
                final_score=float(item["final_score"]),
                content=doc.page_content,
            )
        )

    return ResolveResponse(
        mode="live",
        escalation_text=payload.escalation_text,
        likely_issue=response.likely_issue,
        recommended_next_step=response.recommended_next_step,
        recommended_owner=response.recommended_owner.value,
        recommended_queue=response.recommended_queue,
        requires_human_handoff=response.requires_human_handoff,
        handoff_reason=response.handoff_reason,
        evidence_ids=response.evidence_ids,
        warning_type=response.warning_type.value,
        warning_message=response.warning_message,
        insufficient_evidence=response.insufficient_evidence,
        retrieved_chunks=retrieved_chunks,
    )


@app.get("/")
def serve_app() -> FileResponse:
    return FileResponse(WEB_DIR / "app.html")


@app.get("/app.js")
def serve_js() -> FileResponse:
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript")


@app.get("/styles.css")
def serve_css() -> FileResponse:
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "model": settings.openai_model,
    }


@app.get("/demo", response_model=ResolveResponse)
def get_demo() -> ResolveResponse:
    if not DEMO_RESPONSE_PATH.exists():
        raise HTTPException(status_code=404, detail="Demo response file not found.")

    payload = json.loads(DEMO_RESPONSE_PATH.read_text(encoding="utf-8"))
    return ResolveResponse.model_validate(payload)


def check_live_access(x_access_token: str | None) -> None:
    if not x_access_token:
        raise HTTPException(status_code=401, detail="Missing access token.")

    if x_access_token != APP_ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid access token.")

    used = live_usage_by_token.get(x_access_token, 0)
    if used >= LIVE_REQUEST_LIMIT:
        raise HTTPException(status_code=429, detail="Live request limit reached.")

    live_usage_by_token[x_access_token] = used + 1


@app.get("/usage")
def usage(x_access_token: str | None = Header(default=None)) -> dict[str, int]:
    if not x_access_token or x_access_token != APP_ACCESS_TOKEN:
        return {"used": 0, "limit": LIVE_REQUEST_LIMIT}

    return {
        "used": live_usage_by_token.get(x_access_token, 0),
        "limit": LIVE_REQUEST_LIMIT,
    }

@app.post("/auth/check")
def check_auth(x_access_token: str | None = Header(default=None)) -> dict[str, Any]:
    if not x_access_token:
        raise HTTPException(status_code=401, detail="Missing access token.")

    if x_access_token != APP_ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid access token.")

    used = live_usage_by_token.get(x_access_token, 0)

    return {
        "valid": True,
        "used": used,
        "limit": LIVE_REQUEST_LIMIT,
        "remaining": max(LIVE_REQUEST_LIMIT - used, 0),
    }

@app.post("/resolve", response_model=ResolveResponse)
def resolve_escalation(
    payload: ResolveRequest,
    x_access_token: str | None = Header(default=None),
) -> ResolveResponse:
    check_live_access(x_access_token)
    return build_live_response(payload)