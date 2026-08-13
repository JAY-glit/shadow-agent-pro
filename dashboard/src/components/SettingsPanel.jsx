import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import apiClient from "../api/axiosClient.js";

const STATUS_ICON = {
  ok: { icon: CheckCircle2, color: "#43a047" },
  unavailable: { icon: XCircle, color: "#8a8f98" },
  not_loaded: { icon: AlertCircle, color: "#fb8c00" },
  no_key: { icon: XCircle, color: "#8a8f98" },
  error: { icon: XCircle, color: "#e53935" },
};

const DESCRIPTIONS = {
  database: "Stores threat records and scan logs.",
  redis: "Powers caching, the async deep-scan pipeline, and live WebSocket push across processes.",
  ml_model: "Random Forest trained on 25+ lexical/domain/SSL features.",
  char_ngram_model: "Independent second-opinion classifier over raw character patterns.",
  virustotal: "Cross-checks URLs against 70+ antivirus engines.",
  safe_browsing: "Google's continuously updated malicious-site database.",
};

export default function SettingsPanel() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    apiClient.get("/status").then((r) => setStatus(r.data)).catch(() => setStatus(null));
  }, []);

  return (
    <div className="settings-page">
      <section className="panel">
        <h2>Detection Pipeline Configuration</h2>
        {status ? (
          <div className="settings-list">
            {Object.entries(status.checks).map(([key, check]) => {
              const meta = STATUS_ICON[check.status] || STATUS_ICON.error;
              const Icon = meta.icon;
              return (
                <div key={key} className="settings-row">
                  <Icon size={18} color={meta.color} />
                  <div className="settings-row__body">
                    <div className="settings-row__name">{key.replace(/_/g, " ")}</div>
                    <div className="settings-row__desc">{DESCRIPTIONS[key] || ""}</div>
                    {check.note && <div className="settings-row__note">{check.note}</div>}
                  </div>
                  <span className="settings-row__status" style={{ color: meta.color }}>
                    {check.status.replace(/_/g, " ")}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="empty">Could not reach the status endpoint.</p>
        )}
      </section>

      <section className="panel">
        <h2>API Keys</h2>
        <p className="settings-help">
          VirusTotal and Google Safe Browsing keys are configured server-side in <code>backend/.env</code> —
          copy <code>backend/.env.example</code> to get started. Free tiers work fine for development.
        </p>
        <div className="settings-links">
          <a href="https://www.virustotal.com/gui/join-us" target="_blank" rel="noreferrer">Get a VirusTotal key →</a>
          <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer">Get a Safe Browsing key →</a>
        </div>
      </section>

      <section className="panel">
        <h2>About</h2>
        <p className="settings-help">
          Shadow Agent Pro — real-time malware &amp; phishing detection combining a Chrome extension,
          Flask API, and this dashboard. Detection uses an ensemble of a Random Forest over engineered
          URL/domain/SSL features and an independent character n-gram model, cross-checked against
          VirusTotal and Google Safe Browsing when configured.
        </p>
      </section>
    </div>
  );
}
