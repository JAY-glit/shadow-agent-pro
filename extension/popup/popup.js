// popup.js — reads the last scan result for the active tab from storage
// and renders a color-coded verdict, confidence bar, and (when available)
// the two-model ensemble breakdown.

const statusEl = document.getElementById("status");
const statusText = document.getElementById("status-text");
const detailsEl = document.getElementById("details");
const reportBtn = document.getElementById("report-btn");
const confidenceRow = document.getElementById("confidence-row");
const confidenceBarFill = document.getElementById("confidence-bar-fill");
const confidenceLabel = document.getElementById("confidence-label");
const ensembleEl = document.getElementById("ensemble");
const charNgramScoreEl = document.getElementById("char-ngram-score");

const VERDICT_META = {
  safe: { label: "Safe", className: "status--safe", color: "#43a047" },
  suspicious: { label: "Suspicious", className: "status--suspicious", color: "#fb8c00" },
  malicious: { label: "Malicious — Blocked", className: "status--malicious", color: "#e53935" },
};

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const key = `scan:${tab.id}`;
  const { [key]: result } = await chrome.storage.local.get(key);

  if (!result) {
    statusText.textContent = "No scan data yet for this page.";
    return;
  }

  const meta = VERDICT_META[result.verdict] || VERDICT_META.suspicious;
  statusEl.className = `status ${meta.className}`;
  statusText.textContent = `${meta.label} · ${Math.round(result.confidence * 100)}% confidence`;

  confidenceRow.style.display = "block";
  confidenceBarFill.style.width = `${Math.round(result.confidence * 100)}%`;
  confidenceBarFill.style.background = meta.color;
  confidenceLabel.textContent = `${Math.round(result.confidence * 100)}% overall confidence`;

  if (result.char_ngram_score != null) {
    ensembleEl.style.display = "block";
    charNgramScoreEl.textContent = `${Math.round(result.char_ngram_score * 100)}% malicious`;
  }

  detailsEl.innerHTML = (result.reasons || [])
    .map((r) => `<li>${r}</li>`)
    .join("");
}

reportBtn.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await fetch("http://localhost:5000/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: tab.url }),
  });
  reportBtn.textContent = "Thanks — feedback logged";
  reportBtn.disabled = true;
});

init();
