import { useEffect, useMemo, useRef, useState } from "react";
import { Search, LayoutDashboard, ListTree, BarChart3, Settings, Activity, Zap } from "lucide-react";

const NAV_COMMANDS = [
  { id: "nav-overview", label: "Go to Overview", icon: LayoutDashboard, action: (ctx) => ctx.navigate("overview") },
  { id: "nav-threats", label: "Go to Threats", icon: ListTree, action: (ctx) => ctx.navigate("threats") },
  { id: "nav-analytics", label: "Go to Analytics", icon: BarChart3, action: (ctx) => ctx.navigate("analytics") },
  { id: "nav-liveops", label: "Go to Live Ops", icon: Activity, action: (ctx) => ctx.navigate("liveops") },
  { id: "nav-settings", label: "Go to Settings", icon: Settings, action: (ctx) => ctx.navigate("settings") },
];

function looksLikeUrl(value) {
  return /^https?:\/\/.+\..+/.test(value.trim()) || /^[a-z0-9-]+\.[a-z]{2,}/i.test(value.trim());
}

/**
 * Cmd+K / Ctrl+K opens this. Two kinds of entries: static navigation
 * commands (filtered by fuzzy-ish substring match) and, if the typed text
 * looks like a URL, a dynamic "Scan this URL" action — so a person can go
 * from "I want to check this link" to a result without ever touching the
 * mouse.
 */
export default function CommandPalette({ open, onClose, onNavigate, onScanUrl }) {
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 10);
    }
  }, [open]);

  const filteredNav = useMemo(
    () => NAV_COMMANDS.filter((c) => c.label.toLowerCase().includes(query.toLowerCase())),
    [query]
  );

  const showScanAction = query.trim().length > 3 && looksLikeUrl(query);

  const handleSelectNav = (cmd) => {
    cmd.action({ navigate: onNavigate });
    onClose();
  };

  const handleScan = () => {
    const url = query.trim().startsWith("http") ? query.trim() : `https://${query.trim()}`;
    onScanUrl(url);
    onClose();
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && open) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="palette-overlay" onClick={onClose}>
      <div className="palette" onClick={(e) => e.stopPropagation()}>
        <div className="palette__input-row">
          <Search size={16} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Navigate, or paste a URL to scan…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && showScanAction) handleScan();
            }}
          />
          <kbd>Esc</kbd>
        </div>

        <div className="palette__results">
          {showScanAction && (
            <button className="palette__item palette__item--action" onClick={handleScan}>
              <Zap size={16} />
              <span>Scan URL: <strong>{query.trim()}</strong></span>
              <kbd>Enter</kbd>
            </button>
          )}

          {filteredNav.map((cmd) => (
            <button key={cmd.id} className="palette__item" onClick={() => handleSelectNav(cmd)}>
              <cmd.icon size={16} />
              <span>{cmd.label}</span>
            </button>
          ))}

          {filteredNav.length === 0 && !showScanAction && (
            <div className="palette__empty">No matching commands.</div>
          )}
        </div>
      </div>
    </div>
  );
}
