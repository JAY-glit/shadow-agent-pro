import { X, ShieldAlert, ShieldQuestion, ShieldCheck } from "lucide-react";

const VERDICT_META = {
  malicious: { color: "#e53935", icon: ShieldAlert, label: "Malicious" },
  suspicious: { color: "#fb8c00", icon: ShieldQuestion, label: "Suspicious" },
  safe: { color: "#43a047", icon: ShieldCheck, label: "Safe" },
};

export default function ThreatDetailDrawer({ threat, onClose }) {
  if (!threat) return null;

  const meta = VERDICT_META[threat.verdict] || VERDICT_META.suspicious;
  const Icon = meta.icon;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer__header">
          <div className="drawer__title-row">
            <Icon size={20} color={meta.color} />
            <h2>{meta.label}</h2>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="drawer__url" title={threat.url}>{threat.url}</div>
        <div className="drawer__domain">{threat.domain}</div>

        <div className="drawer__confidence">
          <div className="drawer__confidence-bar-track">
            <div
              className="drawer__confidence-bar-fill"
              style={{ width: `${Math.round(threat.confidence * 100)}%`, background: meta.color }}
            />
          </div>
          <span>{Math.round(threat.confidence * 100)}% overall confidence</span>
        </div>

        <div className="drawer__section">
          <h3>Ensemble breakdown</h3>
          <div className="drawer__model-row">
            <span>Random Forest + engineered features</span>
            <span className="drawer__model-weight">65% weight</span>
          </div>
          {threat.char_ngram_score != null ? (
            <div className="drawer__model-row">
              <span>Character n-gram (independent second opinion)</span>
              <span className="drawer__model-weight">
                35% weight · {Math.round(threat.char_ngram_score * 100)}% malicious
              </span>
            </div>
          ) : (
            <div className="drawer__model-row drawer__model-row--muted">
              <span>Character n-gram model</span>
              <span>not available for this scan</span>
            </div>
          )}
        </div>

        <div className="drawer__section">
          <h3>Why this verdict</h3>
          {threat.reasons?.length > 0 ? (
            <ul className="drawer__reasons">
              {threat.reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          ) : (
            <p className="empty">No specific signals recorded — verdict based on overall model confidence.</p>
          )}
        </div>

        <div className="drawer__section">
          <h3>Detected</h3>
          <p>{new Date(threat.detected_at).toLocaleString()}</p>
        </div>
      </aside>
    </div>
  );
}
