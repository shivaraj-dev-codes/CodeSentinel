/**
 * WebSocket hook for real-time scan progress updates.
 * Connects to WS /ws/scans/{scanId}/ and dispatches updates to Zustand.
 */
import { useEffect, useRef } from "react";
import { useScanStore } from "../store/scanStore";

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? `ws://${window.location.host}`;

interface ProgressMessage {
  type: string;
  scan_id: string;
  percent: number;
  status: string;
  message: string;
}

export function useScanWebSocket(scanId: string | null, enabled = true) {
  const setProgress = useScanStore((s) => s.setProgress);
  const clearProgress = useScanStore((s) => s.clearProgress);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const shouldReconnect = useRef(true);

  useEffect(() => {
    if (!scanId || !enabled) return;

    shouldReconnect.current = true;

    function connect() {
      if (!scanId) return;
      const url = `${WS_BASE}/ws/scans/${scanId}/`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setProgress(scanId, { isConnected: true });
      };

      ws.onmessage = (event) => {
        try {
          const msg: ProgressMessage = JSON.parse(event.data);
          setProgress(scanId, {
            percent: msg.percent,
            status: msg.status,
            message: msg.message,
          });

          // Disconnect when scan finishes
          if (msg.status === "completed" || msg.status === "failed") {
            shouldReconnect.current = false;
            ws.close();
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onerror = () => {
        setProgress(scanId, { isConnected: false });
      };

      ws.onclose = () => {
        setProgress(scanId, { isConnected: false });
        if (shouldReconnect.current) {
          reconnectTimer.current = setTimeout(connect, 3000);
        }
      };
    }

    connect();

    return () => {
      shouldReconnect.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      clearProgress(scanId);
    };
  }, [scanId, enabled, setProgress, clearProgress]);
}
