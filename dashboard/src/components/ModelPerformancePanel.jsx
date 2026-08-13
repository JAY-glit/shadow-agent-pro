import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis } from "recharts";
import apiClient from "../api/axiosClient.js";

const VERDICT_COLORS = { malicious: "#e53935", suspicious: "#fb8c00", safe: "#43a047" };

export default function ModelPerformancePanel({ stats }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [drift, setDrift] = useState(null);
  const [importance, setImportance] = useState(null);

  useEffect(() => {
    apiClient.get("/model/version").then((r) => setModelInfo(r.data)).catch(() => {});
    apiClient.get("/model/drift").then((r) => setDrift(r.data)).catch(() => {});
    apiClient.get("/model/feature-importance").then((r) => setImportance(r.data)).catch(() => {});
  }, []);

  const verdictData = stats
    ? [
        { name: "Safe", value: stats.safe || 0, color: VERDICT_COLORS.safe },
        { name: "Suspicious", value: stats.suspicious || 0, color: VERDICT_COLORS.suspicious },
        { name: "Malicious", value: stats.malicious || 0, color: VERDICT_COLORS.malicious },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="analytics-grid">
      <section className="panel">
        <h2>Verdict Distribution</h2>
        {verdictData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={verdictData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={3}>
                {verdictData.map((d) => <Cell key={d.name} fill={d.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#1f2229", border: "1px solid #333" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <p className="empty">No scans recorded yet.</p>
        )}
      </section>

      <section className="panel">
        <h2>Model Info</h2>
        {modelInfo ? (
          <div className="model-info-grid">
            <div className="model-info-row"><span>Version</span><span>{modelInfo.version}</span></div>
            <div className="model-info-row"><span>Trained</span><span>{modelInfo.trained_at ? new Date(modelInfo.trained_at).toLocaleString() : "—"}</span></div>
            <div className="model-info-row"><span>ROC-AUC</span><span>{modelInfo.metrics?.roc_auc ?? "—"}</span></div>
            <div className="model-info-row"><span>Training samples</span><span>{modelInfo.metrics?.n_train ?? "—"}</span></div>
            <div className="model-info-row"><span>Test samples</span><span>{modelInfo.metrics?.n_test ?? "—"}</span></div>
            <div className="model-info-row"><span>Baseline malicious rate</span><span>{modelInfo.baseline_malicious_rate != null ? `${Math.round(modelInfo.baseline_malicious_rate * 100)}%` : "—"}</span></div>
          </div>
        ) : (
          <p className="empty">Model metadata unavailable — train a model first.</p>
        )}
      </section>

      <section className="panel analytics-grid__wide">
        <h2>Drift Monitor</h2>
        {drift && drift.status !== "no_data" ? (
          <div className="drift-panel">
            <span className={`status-pill drift-pill--${drift.status}`}>
              {drift.status === "drift_detected" ? "Drift detected" : drift.status === "no_baseline" ? "No baseline" : "Stable"}
            </span>
            {drift.current_malicious_rate != null && (
              <p>
                Current malicious rate over last {drift.sample_size} scans:{" "}
                <strong>{Math.round(drift.current_malicious_rate * 100)}%</strong>
                {drift.baseline_malicious_rate != null && (
                  <> vs. training baseline of <strong>{Math.round(drift.baseline_malicious_rate * 100)}%</strong></>
                )}
              </p>
            )}
            {drift.recommendation && <p className="drift-recommendation">{drift.recommendation}</p>}
          </div>
        ) : (
          <p className="empty">Not enough scan history yet to evaluate drift.</p>
        )}
      </section>

      <section className="panel analytics-grid__wide">
        <h2>Feature Importance</h2>
        <p className="settings-help" style={{ marginBottom: "12px" }}>
          Which engineered features the Random Forest relies on most, across all of training —
          a coarser, whole-model view than the per-scan SHAP explanations shown in the threat detail drawer.
        </p>
        {importance?.status === "ok" && importance.features.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={importance.features.slice(0, 10)} layout="vertical" margin={{ left: 40 }}>
              <XAxis type="number" stroke="#8a8f9c" fontSize={11} />
              <YAxis type="category" dataKey="name" stroke="#8a8f9c" fontSize={11} width={140} />
              <Tooltip contentStyle={{ background: "#1f2229", border: "1px solid #333" }} />
              <Bar dataKey="importance" fill="#5b7cfa" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="empty">
            {importance?.status === "model_not_loaded"
              ? "No trained model loaded yet — run the training pipeline first."
              : "Feature importance unavailable."}
          </p>
        )}
      </section>
    </div>
  );
}
