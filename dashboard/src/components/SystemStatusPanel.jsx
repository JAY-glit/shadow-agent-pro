import { useEffect, useState } from "react";
import apiClient from "../api/axiosClient.js";

const STATUS_COLORS = {
  ok: "#43a047",
  healthy: "#43a047",
  degraded: "#fb8c00",
  unhealthy: "#e53935",
  unavailable: "#8a8f98",
  not_loaded: "#8a8f98",
  no_key: "#8a8f98",
  error: "#e53935",
};

const LABELS = {
  database: "Database",
  redis: "Redis / Cache",
  ml_model: "ML Model",
  char_ngram_model: "Char N-gram Model",
  virustotal: "VirusTotal",
  safe_browsing: "Safe Browsing",
};

/**
 * A one-glance system health panel — the kind of thing a real SaaS status
 * page is built on. Doubles as a fast way to answer "why does this scan
 * look off" during a demo without digging through logs.
 */
export default function SystemStatusPanel() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchStatus = () =>
      apiClient
        .get("/status")
        .then((r) => setData(r.data))
        .catch(() => setData(null));

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!data) return null;

  return (
    <section className="panel status-panel">
      <div className="status-panel__header">
        <h2>System Status</h2>
        <span
          className="status-pill"
          style={{ background: STATUS_COLORS[data.overall] || "#8a8f98" }}
        >
          {data.overall}
        </span>
      </div>
      <div className="status-grid">
        {Object.entries(data.checks).map(([key, check]) => (
          <div key={key} className="status-item" title={check.note || ""}>
            <span
              className="status-dot"
              style={{ background: STATUS_COLORS[check.status] || "#8a8f98" }}
            />
            <span>{LABELS[key] || key}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
