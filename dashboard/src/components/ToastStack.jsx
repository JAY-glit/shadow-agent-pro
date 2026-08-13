import { useCallback, useRef, useState } from "react";
import { ShieldAlert, ShieldQuestion, X } from "lucide-react";

const ICONS = { malicious: ShieldAlert, suspicious: ShieldQuestion };
const COLORS = { malicious: "#e53935", suspicious: "#fb8c00" };
const AUTO_DISMISS_MS = 6000;

/**
 * A small toast stack in the corner of the screen. Kept separate from
 * AlertBanner (which is for the manual scanner's own result) — this one
 * is driven entirely by the live socket feed, so threats detected from
 * ANY source (extension, another dashboard tab, another user) surface
 * here without the person having to be looking at the right panel.
 */
export function useToasts() {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const pushToast = useCallback((threat) => {
    if (threat.verdict === "safe") return; // only surface things worth noticing
    const id = idRef.current++;
    setToasts((prev) => [...prev, { ...threat, _id: id }].slice(-4)); // cap stack at 4
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t._id !== id));
    }, AUTO_DISMISS_MS);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t._id !== id));
  }, []);

  return { toasts, pushToast, dismissToast };
}

export default function ToastStack({ toasts, onDismiss }) {
  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack">
      {toasts.map((t) => {
        const Icon = ICONS[t.verdict] || ShieldQuestion;
        const color = COLORS[t.verdict] || "#8a8f98";
        return (
          <div key={t._id} className="toast" style={{ borderColor: color }}>
            <Icon size={16} color={color} />
            <div className="toast__body">
              <div className="toast__title" style={{ color }}>
                {t.verdict === "malicious" ? "Malicious URL blocked" : "Suspicious URL detected"}
              </div>
              <div className="toast__url" title={t.url}>{t.url}</div>
            </div>
            <button className="icon-btn" onClick={() => onDismiss(t._id)}>
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
