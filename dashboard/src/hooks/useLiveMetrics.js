import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import apiClient from "../api/axiosClient.js";

const SOCKET_URL = "http://localhost:5000";

/**
 * Live operational metrics: requests/min, latency percentiles, verdict
 * split, and a time-bucketed volume series for the sparkline. Fetches an
 * initial snapshot over REST, then updates live from the 'metrics_update'
 * socket event pushed on every scan — no polling needed once connected.
 */
export default function useLiveMetrics() {
  const [metrics, setMetrics] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    apiClient.get("/metrics").then((r) => setMetrics(r.data)).catch(() => {});

    // See LiveActivityFeed.jsx for why this forces polling-only (upgrade: false)
    const socket = io(SOCKET_URL, { transports: ["polling"], upgrade: false });
    socketRef.current = socket;
    socket.on("metrics_update", (data) => setMetrics(data));

    return () => socket.disconnect();
  }, []);

  return metrics;
}
