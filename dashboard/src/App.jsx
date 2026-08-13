import { useEffect, useState, useCallback } from "react";
import { Bell } from "lucide-react";
import Sidebar from "./components/Sidebar.jsx";
import StatisticsPanel from "./components/StatisticsPanel.jsx";
import ThreatTable from "./components/ThreatTable.jsx";
import AlertBanner from "./components/AlertBanner.jsx";
import URLScanner from "./components/URLScanner.jsx";
import HistoryChart from "./components/HistoryChart.jsx";
import LiveActivityFeed from "./components/LiveActivityFeed.jsx";
import GeoThreatPanel from "./components/GeoThreatPanel.jsx";
import SystemStatusPanel from "./components/SystemStatusPanel.jsx";
import ThreatDetailDrawer from "./components/ThreatDetailDrawer.jsx";
import ModelPerformancePanel from "./components/ModelPerformancePanel.jsx";
import SettingsPanel from "./components/SettingsPanel.jsx";
import LiveOpsPanel from "./components/LiveOpsPanel.jsx";
import CommandPalette from "./components/CommandPalette.jsx";
import ToastStack, { useToasts } from "./components/ToastStack.jsx";
import { fetchStats, fetchThreats, scanUrl } from "./api/axiosClient.js";
import useLiveThreatFeed from "./hooks/useLiveThreatFeed.js";

const TAB_TITLES = {
  overview: "Overview",
  threats: "Threats",
  analytics: "Analytics",
  liveops: "Live Ops",
  settings: "Settings",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState(null);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const { toasts, pushToast, dismissToast } = useToasts();

  const refresh = useCallback(async () => {
    try {
      const [statsData, threatsData] = await Promise.all([fetchStats(), fetchThreats(100)]);
      setStats(statsData);
      setThreats(threatsData);
    } catch (err) {
      setBanner({ type: "error", message: "Could not reach the Shadow Agent Pro API." });
    } finally {
      setLoading(false);
    }
  }, []);

  const { connected } = useLiveThreatFeed((incoming) => {
    setThreats((prev) => [incoming, ...prev].slice(0, 100));
    pushToast(incoming);
    if (incoming.verdict !== "safe") {
      setNotifications((prev) => [incoming, ...prev].slice(0, 20));
    }
    setStats((prev) =>
      prev
        ? {
            ...prev,
            total_scans: (prev.total_scans || 0) + 1,
            [incoming.verdict]: (prev[incoming.verdict] || 0) + 1,
          }
        : prev
    );
  });

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Global Cmd+K / Ctrl+K listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleScanResult = (result) => {
    setBanner({
      type: result.verdict === "malicious" ? "error" : result.verdict === "suspicious" ? "warning" : "success",
      message: `Verdict: ${result.verdict} (${Math.round(result.confidence * 100)}% confidence)${result.cached ? " — cached" : ""}`,
    });
    refresh();
  };

  const handlePaletteScan = async (url) => {
    setActiveTab("overview");
    try {
      const result = await scanUrl(url);
      handleScanResult(result);
    } catch {
      setBanner({ type: "error", message: `Could not scan ${url}` });
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        active={activeTab}
        onNavigate={setActiveTab}
        liveConnected={connected}
        onOpenPalette={() => setPaletteOpen(true)}
      />

      <main className="app-main">
        <header className="app-main__header">
          <h1>{TAB_TITLES[activeTab]}</h1>

          <div className="notif-wrap">
            <button className="icon-btn notif-bell" onClick={() => setNotifOpen((v) => !v)}>
              <Bell size={18} />
              {notifications.length > 0 && <span className="notif-badge">{notifications.length}</span>}
            </button>
            {notifOpen && (
              <div className="notif-dropdown">
                <div className="notif-dropdown__header">
                  <span>Recent alerts</span>
                  {notifications.length > 0 && (
                    <button className="notif-clear" onClick={() => setNotifications([])}>Clear</button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <p className="empty" style={{ padding: "16px" }}>No alerts yet.</p>
                ) : (
                  notifications.map((n, i) => (
                    <div key={i} className="notif-row">
                      <span className={`badge badge--${n.verdict}`}>{n.verdict}</span>
                      <span className="notif-row__url" title={n.url}>{n.url}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </header>

        {banner && <AlertBanner {...banner} onDismiss={() => setBanner(null)} />}

        {activeTab === "overview" && (
          <>
            <SystemStatusPanel />
            <URLScanner onScanned={handleScanResult} />
            {loading ? (
              <div className="skeleton-row">
                <div className="skeleton skeleton--card" />
                <div className="skeleton skeleton--card" />
                <div className="skeleton skeleton--card" />
              </div>
            ) : (
              <StatisticsPanel stats={stats} />
            )}
            <div className="two-col">
              <HistoryChart threats={threats} />
              <LiveActivityFeed />
            </div>
          </>
        )}

        {activeTab === "threats" && (
          <ThreatTable threats={threats} onDeleted={refresh} onSelect={setSelectedThreat} />
        )}

        {activeTab === "analytics" && (
          <>
            <ModelPerformancePanel stats={stats} />
            <GeoThreatPanel />
          </>
        )}

        {activeTab === "liveops" && <LiveOpsPanel />}

        {activeTab === "settings" && <SettingsPanel />}
      </main>

      <ThreatDetailDrawer threat={selectedThreat} onClose={() => setSelectedThreat(null)} />
      <ToastStack toasts={toasts} onDismiss={dismissToast} />
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigate={setActiveTab}
        onScanUrl={handlePaletteScan}
      />
    </div>
  );
}
