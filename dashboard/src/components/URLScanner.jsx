import { useEffect, useRef, useState } from "react";
import { scanUrl } from "../api/axiosClient.js";

const DEBOUNCE_MS = 600;

export default function URLScanner({ onScanned }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [livePreview, setLivePreview] = useState(null);
  const debounceRef = useRef(null);

  // Live-as-you-type preview: debounced so it only fires once typing pauses,
  // giving an instant read without spamming the API on every keystroke.
  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (!looksLikeUrl(url)) {
      setLivePreview(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await scanUrl(url.trim());
        setLivePreview(result);
      } catch {
        setLivePreview(null);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(debounceRef.current);
  }, [url]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    try {
      const result = livePreview || (await scanUrl(url.trim()));
      onScanned?.(result);
      setUrl("");
      setLivePreview(null);
    } catch (err) {
      onScanned?.({ verdict: "error", confidence: 0 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h2>Manual URL Scan</h2>
      <form className="url-scanner" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Scanning…" : "Scan"}
        </button>
      </form>

      {livePreview && (
        <div className={`live-preview live-preview--${livePreview.verdict}`}>
          {livePreview.verdict} · {Math.round(livePreview.confidence * 100)}% confidence
          {livePreview.deep_scan_pending && <span className="live-preview__pending"> — deep scan running…</span>}
        </div>
      )}
    </section>
  );
}

function looksLikeUrl(value) {
  return /^https?:\/\/.+\..+/.test(value.trim());
}
