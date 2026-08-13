import { ShieldCheck, LayoutDashboard, ListTree, BarChart3, Settings, Activity, Circle, Command } from "lucide-react";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "threats", label: "Threats", icon: ListTree },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "liveops", label: "Live Ops", icon: Activity },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ active, onNavigate, liveConnected, onOpenPalette }) {
  return (
    <nav className="sidebar">
      <div className="sidebar__brand">
        <ShieldCheck size={22} strokeWidth={2.25} className="sidebar__brand-icon" />
        <div>
          <div className="sidebar__brand-name">Shadow Agent Pro</div>
          <div className="sidebar__brand-tag">Threat Detection Platform</div>
        </div>
      </div>

      <button className="sidebar__palette-btn" onClick={onOpenPalette}>
        <Command size={14} />
        <span>Quick actions</span>
        <kbd>⌘K</kbd>
      </button>

      <ul className="sidebar__nav">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <li key={id}>
            <button
              className={`sidebar__nav-item ${active === id ? "sidebar__nav-item--active" : ""}`}
              onClick={() => onNavigate(id)}
            >
              <Icon size={17} strokeWidth={2} />
              <span>{label}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className="sidebar__footer">
        <Circle size={8} className={`live-indicator ${liveConnected ? "live-indicator--on" : ""}`} />
        <span>{liveConnected ? "Live feed connected" : "Live feed offline"}</span>
      </div>
    </nav>
  );
}
