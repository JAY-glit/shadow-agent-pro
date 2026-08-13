import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5000";

/**
 * Subscribes to the backend's Socket.IO threat feed. Returns the most
 * recently pushed threat and a live connection flag, so components can
 * react instantly instead of waiting on the polling interval in App.jsx.
 */
export default function useLiveThreatFeed(onNewThreat) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // See LiveActivityFeed.jsx for why this forces polling-only (upgrade: false)
    const socket = io(SOCKET_URL, { transports: ["polling"], upgrade: false });
    socketRef.current = socket;

    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("new_threat", (threat) => onNewThreat?.(threat));

    return () => socket.disconnect();
  }, [onNewThreat]);

  return { connected };
}
