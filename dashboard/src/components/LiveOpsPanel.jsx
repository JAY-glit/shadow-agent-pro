import { AreaChart, Area, ResponsiveContainer, XAxis, Tooltip } from "recharts";
import { Activity, Zap, Gauge, TrendingUp } from "lucide-react";
import useLiveMetrics from "../hooks/useLiveMetrics.js";

const METRIC_CARDS = [
  { key: "requests_per_minute", label: "Requests / min", icon: Activity, suffix: "" },
  { key: "avg_latency_ms", label: "Avg Latency", icon: Zap, suffix: "ms" },
  { key: "p95_latency_ms", label: "p95 Latency", icon: Gauge, suffix: "ms" },
  { key: "total_requests", label: "Total Requests", icon: TrendingUp, suffix: "" },
];

export default function LiveOpsPanel() {
  const metrics = useLiveMetrics();

  const chartData = (metrics?.volume_series || []).map((point) => ({
    time: new Date(point.time * 1000).toLocaleTimeString([], { minute: "2-digit", second: "2-digit" }),
    count: point.count,
  }));

  return (
    <>
      <div className="metric-cards">
        {METRIC_CARDS.map(({ key, label, icon: Icon, suffix }) => (
          <div key={key} className="metric-card">
            <Icon size={16} className="metric-card__icon" />
            <div>
              <div className="metric-card__value">
                {metrics ? `${metrics[key]}${suffix}` : "—"}
              </div>
              <div className="metric-card__label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      <section className="panel">
        <h2>Scan Volume (live)</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#5b7cfa" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#5b7cfa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#8a8f9c" fontSize={11} />
              <Tooltip contentStyle={{ background: "#1f2229", border: "1px solid #333" }} />
              <Area type="monotone" dataKey="count" stroke="#5b7cfa" fill="url(#volumeGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <p className="empty">No scan activity yet — run a scan to see live volume here.</p>
        )}
      </section>
    </>
  );
}
