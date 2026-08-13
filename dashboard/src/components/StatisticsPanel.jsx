export default function StatisticsPanel({ stats }) {
  if (!stats) return <section className="panel">Loading statistics…</section>;

  const cards = [
    { label: "Total Scans", value: stats.total_scans, color: "#546e7a" },
    { label: "Safe", value: stats.safe, color: "#43a047" },
    { label: "Suspicious", value: stats.suspicious, color: "#fb8c00" },
    { label: "Malicious", value: stats.malicious, color: "#e53935" },
  ];

  return (
    <section className="panel stats-panel">
      {cards.map((c) => (
        <div key={c.label} className="stat-card" style={{ borderColor: c.color }}>
          <span className="stat-card__value" style={{ color: c.color }}>{c.value ?? 0}</span>
          <span className="stat-card__label">{c.label}</span>
        </div>
      ))}

      {stats.top_malicious_domains?.length > 0 && (
        <div className="top-domains">
          <h3>Top Malicious Domains</h3>
          <ul>
            {stats.top_malicious_domains.map((d) => (
              <li key={d.domain}>{d.domain} — {d.count} hits</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
