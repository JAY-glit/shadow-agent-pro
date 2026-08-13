import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5000";
const MAX_EVENTS = 25;

const VERDICT_COLORS = { malicious: "#e53935", suspicious: "#fb8c00", safe: "#43a047" };

/**
 * Shows every scan as it happens (not just confirmed threats) — a raw
 * pulse of activity so a viva demo can show the system actually working
 * in real time rather than a static table that updates on refresh.
 */
export default function LiveActivityFeed() {
  const [events, setEvents] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    // transports: ["polling"] + upgrade: false is deliberate, not a
    // downgrade: Socket.IO's default behavior still automatically tries
    // to upgrade from polling to native WebSocket even without forcing
    // transports: ["websocket"] explicitly. On this project's dev setup
    // (Werkzeug's development server + engineio's simple-websocket
    // driver on Windows), that upgrade attempt itself fails server-side
    // with a raw ConnectionError, which the client then treats as a
    // failed connection and retries — creating an endless reconnect loop
    // that floods the backend's logs and, worse, competes for the single-
    // threaded dev server's attention with real API requests. Disabling
    // the upgrade attempt keeps the connection on plain HTTP long-polling
    // the whole time, which is slightly higher latency per update but
    // still comfortably sub-second, and avoids the broken code path
    // entirely rather than retrying into it repeatedly.
    const socket = io(SOCKET_URL, { transports: ["polling"], upgrade: false });
    socketRef.current = socket;

    socket.on("scan_event", (evt) => {
      setEvents((prev) => [{ ...evt, id: crypto.randomUUID(), at: Date.now() }, ...prev].slice(0, MAX_EVENTS));
    });

    return () => socket.disconnect();
  }, []);

  return (
    <section className="panel activity-feed">
      <h2>Live Activity</h2>
      {events.length === 0 && <p className="empty">Waiting for scans…</p>}
      <ul>
        {events.map((e) => (
          <li key={e.id} className="activity-row">
            <span className="activity-dot" style={{ background: VERDICT_COLORS[e.verdict] || "#666" }} />
            <span className="activity-url" title={e.url}>{e.url}</span>
            <span className="activity-source">{e.source}</span>
            <span className="activity-time">{new Date(e.at).toLocaleTimeString()}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
