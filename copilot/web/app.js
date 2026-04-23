const conversationEl = document.getElementById("conversation");
const resolutionEl = document.getElementById("resolutionContent");
const retrievalEl = document.getElementById("retrievalContent");

const metricOwner = document.getElementById("metricOwner");
const metricHandoff = document.getElementById("metricHandoff");
const metricWarning = document.getElementById("metricWarning");
const metricEvidenceCount = document.getElementById("metricEvidenceCount");
const modeBadge = document.getElementById("modeBadge");

const questionInput = document.getElementById("questionInput");
const tokenInput = document.getElementById("tokenInput");
const tokenStatus = document.getElementById("tokenStatus");
const usageText = document.getElementById("usageText");

const demoBtn = document.getElementById("demoBtn");
const sendBtn = document.getElementById("sendBtn");
const unlockBtn = document.getElementById("unlockBtn");
const toggleRetrievalBtn = document.getElementById("toggleRetrievalBtn");

let liveAccessToken = null;
let retrievalExpanded = false;

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const title = document.createElement("div");
  title.className = "message-title";
  title.textContent = role === "user" ? "User input" : "System status";

  const body = document.createElement("div");
  body.textContent = text;

  wrapper.appendChild(title);
  wrapper.appendChild(body);
  conversationEl.appendChild(wrapper);
  conversationEl.scrollTop = conversationEl.scrollHeight;
}

function formatWarningLabel(value) {
  if (!value) return "—";
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function setModeBadge(mode) {
  modeBadge.classList.remove("live", "demo");

  if (mode === "demo") {
    modeBadge.textContent = "Demo mode";
    modeBadge.classList.add("demo");
  } else if (mode === "live") {
    modeBadge.textContent = "Live mode";
    modeBadge.classList.add("live");
  } else {
    modeBadge.textContent = "No response loaded";
  }
}

function warningBadge(payload) {
  const label = escapeHtml(formatWarningLabel(payload.warning_type));

  if (payload.warning_type === "none") {
    return `<span class="badge success">No Warning</span>`;
  }

  if (payload.warning_type === "conflict") {
    return `<span class="badge danger">${label}</span>`;
  }

  if (payload.warning_type === "stale_guidance") {
    return `<span class="badge warning">${label}</span>`;
  }

  if (payload.warning_type === "insufficient_detail") {
    return `<span class="badge warning">${label}</span>`;
  }

  return `<span class="badge warning">${label}</span>`;
}

function evidenceBadge(payload) {
  if (payload.insufficient_evidence) {
    return `<span class="badge danger">Insufficient evidence</span>`;
  }

  return `<span class="badge success">Sufficient evidence</span>`;
}

function renderMetrics(payload) {
  metricOwner.textContent = payload.recommended_owner || "—";
  metricHandoff.textContent = payload.requires_human_handoff ? "Required" : "Not required";
  metricWarning.textContent = formatWarningLabel(payload.warning_type || "—");
  metricEvidenceCount.textContent = String((payload.evidence_ids || []).length);

  metricWarning.className = "metric-value";
  if (payload.warning_type) {
    metricWarning.classList.add(`warning-${payload.warning_type.replaceAll("_", "-")}`);
  }
}

function renderResolution(payload) {
  const evidenceIds = payload.evidence_ids && payload.evidence_ids.length
    ? payload.evidence_ids.map((id) => `<div class="inline-code">${escapeHtml(id)}</div>`).join("")
    : `<div class="empty-state">No evidence IDs returned.</div>`;

  resolutionEl.innerHTML = `
    <div class="detail-stack">
      <div class="detail-block">
        <div class="detail-label">Likely issue</div>
        <div>${escapeHtml(payload.likely_issue || "—")}</div>
      </div>

      <div class="detail-block">
        <div class="detail-label">Recommended next step</div>
        <div>${escapeHtml(payload.recommended_next_step || "—")}</div>
      </div>

      <div class="detail-block">
        <div class="detail-label">Warnings</div>
        <div class="badges">
          ${warningBadge(payload)}
          ${evidenceBadge(payload)}
        </div>
        <div style="margin-top:10px;">${escapeHtml(payload.warning_message || "No additional warning message.")}</div>
      </div>

      <div class="detail-block">
        <div class="detail-label">Evidence IDs</div>
        ${evidenceIds}
      </div>
    </div>
  `;
}

function renderRetrieval(payload) {
  const chunks = payload.retrieved_chunks || [];
  if (!chunks.length) {
    retrievalEl.innerHTML = `<div class="empty-state">No retrieved chunks available.</div>`;
    return;
  }

  retrievalEl.innerHTML = chunks
    .map(
      (chunk) => `
        <div class="chunk-card">
          <div class="chunk-title">${escapeHtml(chunk.title || "Untitled chunk")}</div>
          <div class="chunk-meta">
            ${escapeHtml(chunk.file_name || "unknown file")} ·
            ${escapeHtml(chunk.section_title || "unknown section")} ·
            ${escapeHtml(chunk.document_type || "unknown type")} ·
            version ${escapeHtml(chunk.version || "n/a")} ·
            score ${Number(chunk.final_score).toFixed(3)}
          </div>
          <div class="chunk-meta" style="margin-top:6px;">
            Chunk ID: <span class="inline-code">${escapeHtml(chunk.chunk_id || "n/a")}</span>
          </div>
          ${
            chunk.content
              ? `<div class="chunk-content">${escapeHtml(chunk.content)}</div>`
              : ""
          }
        </div>
      `
    )
    .join("");
}

function setRetrievalExpanded(expanded) {
  retrievalExpanded = expanded;
  retrievalEl.className = expanded ? "retrieval-expanded" : "retrieval-collapsed";
  toggleRetrievalBtn.textContent = expanded ? "Hide" : "Show";
}

async function runDemo() {
  try {
    const res = await fetch("/demo");
    const payload = await res.json();

    if (!res.ok) {
      throw new Error(payload.detail || "Failed to load demo response.");
    }

    conversationEl.innerHTML = "";
    addMessage("user", payload.escalation_text || "Demo example loaded.");
    addMessage("system", "Stored demo response loaded successfully. No live inference was used.");

    setModeBadge(payload.mode);
    renderMetrics(payload);
    renderResolution(payload);
    renderRetrieval(payload);
    setRetrievalExpanded(false);
  } catch (err) {
    addMessage("system", `Demo error: ${err.message}`);
  }
}

async function checkUsage() {
  try {
    const headers = liveAccessToken ? { "x-access-token": liveAccessToken } : {};
    const res = await fetch("/usage", { headers });
    const payload = await res.json();
    usageText.textContent = `Live usage: ${payload.used}/${payload.limit}`;
  } catch (err) {
    usageText.textContent = "Could not load usage.";
  }
}

async function unlockLiveMode() {
  const token = tokenInput.value.trim();

  if (!token) {
    tokenStatus.className = "status-line error";
    tokenStatus.textContent = "Please enter a protection token.";
    return;
  }

  try {
    const res = await fetch("/auth/check", {
      method: "POST",
      headers: {
        "x-access-token": token,
      },
    });

    const payload = await res.json();

    if (!res.ok) {
      throw new Error(payload.detail || "Token validation failed.");
    }

    liveAccessToken = token;
    sendBtn.disabled = false;

    tokenInput.value = "";
    tokenStatus.className = "status-line success";
    tokenStatus.textContent = `Live mode unlocked. Remaining requests: ${payload.remaining}`;
    usageText.textContent = `Live usage: ${payload.used}/${payload.limit}`;
  } catch (err) {
    liveAccessToken = null;
    sendBtn.disabled = true;
    tokenInput.value = "";
    tokenStatus.className = "status-line error";
    tokenStatus.textContent = `Access denied: ${err.message}`;
  }
}

async function sendLiveRequest() {
  const question = questionInput.value.trim();

  if (!question) {
    addMessage("system", "Please enter an escalation question first.");
    return;
  }

  if (!liveAccessToken) {
    addMessage("system", "Live mode is locked. Validate the protection token first.");
    return;
  }

  const submittedQuestion = question;
  questionInput.value = "";

  addMessage("user", submittedQuestion);

  try {
    const res = await fetch("/resolve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-access-token": liveAccessToken,
      },
      body: JSON.stringify({
        escalation_text: submittedQuestion,
        top_k: 5,
      }),
    });

    const payload = await res.json();

    if (!res.ok) {
      throw new Error(payload.detail || "Live request failed.");
    }

    addMessage("system", "Live response generated successfully.");

    setModeBadge(payload.mode);
    renderMetrics(payload);
    renderResolution(payload);
    renderRetrieval(payload);
    setRetrievalExpanded(false);
    await checkUsage();
  } catch (err) {
    addMessage("system", `Live error: ${err.message}`);
  }
}

demoBtn.addEventListener("click", runDemo);
sendBtn.addEventListener("click", sendLiveRequest);
unlockBtn.addEventListener("click", unlockLiveMode);
toggleRetrievalBtn.addEventListener("click", () => setRetrievalExpanded(!retrievalExpanded));

setRetrievalExpanded(false);