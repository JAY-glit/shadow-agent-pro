import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function HistoryChart({ threats }) {
  const byHour = groupByHour(threats);

  return (
    <section className="panel">
      <h2>Threat Detections Over Time</h2>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={byHour}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d33" />
          <XAxis dataKey="hour" stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} allowDecimals={false} />
          <Tooltip contentStyle={{ background: "#1f2229", border: "1px solid #333" }} />
          <Line type="monotone" dataKey="malicious" stroke="#e53935" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="suspicious" stroke="#fb8c00" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="safe" stroke="#43a047" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

function groupByHour(threats) {
  const buckets = {};
  for (const t of threats) {
    const hour = new Date(t.detected_at).toISOString().slice(0, 13) + ":00";
    buckets[hour] ??= { hour, safe: 0, suspicious: 0, malicious: 0 };
    buckets[hour][t.verdict] = (buckets[hour][t.verdict] || 0) + 1;
  }
  return Object.values(buckets).sort((a, b) => a.hour.localeCompare(b.hour));
}
