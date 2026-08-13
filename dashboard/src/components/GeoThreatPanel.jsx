import { useEffect, useState } from "react";
import apiClient from "../api/axiosClient.js";

/**
 * Country-level rollup of where confirmed-malicious domains geolocate to.
 * A full map would need a mapping lib; this leaderboard gives the same
 * "where are attacks coming from" insight cheaply and reads well in a demo.
 */
export default function GeoThreatPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get("/geo/threats")
      .then((r) => setData(r.data))
      .catch(() => setData({ points: [], leaderboard: [] }))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <section className="panel">Resolving threat origins…</section>;

  return (
    <section className="panel">
      <h2>Threat Origins by Country</h2>
      {data.leaderboard.length === 0 && <p className="empty">No geolocated threats yet.</p>}
      <ul className="geo-list">
        {data.leaderboard.map((row) => (
          <li key={row.country} className="geo-row">
            <span>{row.country}</span>
            <div className="geo-bar-track">
              <div
                className="geo-bar-fill"
                style={{ width: `${Math.min(100, (row.count / (data.leaderboard[0]?.count || 1)) * 100)}%` }}
              />
            </div>
            <span className="geo-count">{row.count}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
