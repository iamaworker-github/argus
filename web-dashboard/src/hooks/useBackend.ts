import { useState, useEffect, useCallback, useRef } from 'react';
import type { SystemState, LogLine } from '../types';
import { INITIAL_STATE } from '../data/initialState';

let logIdCounter = 1000;

export function useBackend() {
  const [state, setState] = useState<SystemState>({ ...INITIAL_STATE });
  const [selectedAgent, setSelectedAgent] = useState('2');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef(0);

  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws`;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        reconnectRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'state') {
            setState(prev => ({
              ...prev,
              ...data.payload,
              nodes: data.payload.nodes?.length ? data.payload.nodes : prev.nodes,
              edges: data.payload.edges?.length ? data.payload.edges : prev.edges,
              findings: data.payload.findings?.length ? data.payload.findings : prev.findings,
              logs: data.payload.logs
                ? data.payload.logs.map((l: LogLine) => ({ ...l, id: ++logIdCounter }))
                : prev.logs,
              activities: data.payload.activities || prev.activities,
            }));
          }
        } catch { /* ignore parse errors */ }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        const delay = Math.min(1000 * Math.pow(2, reconnectRef.current), 30000);
        reconnectRef.current += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, []);

  const startScan = useCallback(async (target: string, mode?: string) => {
    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, mode: mode || 'pentest' }),
      });
      return await res.json();
    } catch { return null; }
  }, []);

  const stopScan = useCallback(async (scanId: string) => {
    try {
      const res = await fetch(`/api/scan/${scanId}/stop`, { method: 'POST' });
      return await res.json();
    } catch { return null; }
  }, []);

  const getScans = useCallback(async () => {
    try {
      const res = await fetch('/api/scans');
      return await res.json();
    } catch { return []; }
  }, []);

  return {
    state,
    selectedAgent,
    setSelectedAgent,
    connected,
    startScan,
    stopScan,
    getScans,
  };
}
