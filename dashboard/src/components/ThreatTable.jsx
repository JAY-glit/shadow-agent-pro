import { useMemo, useState } from "react";
import { Search, Download, Trash2 } from "lucide-react";
import { deleteThreat } from "../api/axiosClient.js";

const VERDICT_COLORS = {
  malicious: "#e53935",
  suspicious: "#fb8c00",
  safe: "#43a047",
};

export default function ThreatTable({ threats, onDeleted, onSelect }) {
  const [query, setQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("all");

  const filtered = useMemo(() => {
    return threats.filter((t) => {
      const matchesQuery = !query || t.url.toLowerCase().includes(query.toLowerCase()) || t.domain?.toLowerCase().includes(query.toLowerCase());
      const matchesVerdict = verdictFilter === "all" || t.verdict === verdictFilter;
      return matchesQuery && matchesVerdict;
    });
  }, [threats, query, verdictFilter]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    await deleteThreat(id);
    onDeleted?.();
  };

  const exportCsv = () => {
    const header = ["url", "domain", "verdict", "confidence", "char_ngram_score", "detected_at"];
    const rows = filtered.map((t) =>
      [t.url, t.domain, t.verdict, t.confidence, t.char_ngram_score ?? "", t.detected_at]
        .map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`)
        .join(",")
    );
    const csv = [header.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shadow-agent-threats-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="panel">
      <div className="threat-table__header">
        <h2>Threats</h2>
        <div className="threat-table__controls">
          <div className="search-input">
            <Search size={14} />
            <input
              type="text"
              placeholder="Search URL or domain…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <select value={verdictFilter} onChange={(e) => setVerdictFilter(e.target.value)}>
            <option value="all">All verdicts</option>
            <option value="malicious">Malicious</option>
            <option value="suspicious">Suspicious</option>
            <option value="safe">Safe</option>
          </select>
          <button className="btn-secondary" onClick={exportCsv} disabled={filtered.length === 0}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      <table className="threat-table">
        <thead>
          <tr>
            <th>URL</th>
            <th>Domain</th>
            <th>Verdict</th>
            <th>Confidence</th>
            <th>Detected</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((t) => (
            <tr key={t.id} className="threat-table__row" onClick={() => onSelect?.(t)}>
              <td className="truncate" title={t.url}>{t.url}</td>
              <td>{t.domain}</td>
              <td>
                <span className="badge" style={{ background: VERDICT_COLORS[t.verdict] }}>
                  {t.verdict}
                </span>
              </td>
              <td>{Math.round(t.confidence * 100)}%</td>
              <td>{new Date(t.detected_at).toLocaleString()}</td>
              <td>
                <button className="icon-btn" onClick={(e) => handleDelete(e, t.id)}>
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr><td colSpan={6} className="empty">
              {threats.length === 0 ? "No threats recorded yet." : "No threats match your search/filter."}
            </td></tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
