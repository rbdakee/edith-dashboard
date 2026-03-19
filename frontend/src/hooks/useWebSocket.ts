import { useEffect, useRef, useCallback, useState } from 'react';

type WSMessage = {
  type: 'event' | 'agent_state' | 'task_update';
  payload: unknown;
};

export function useWebSocket(token: string, onMessage: (msg: WSMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectTimeout = useRef<number>();

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:18790/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ token }));
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data as string) as WSMessage;
        onMessage(msg);
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect with exponential backoff
      reconnectTimeout.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [token, onMessage]);

  useEffect(() => {
    if (token) connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect, token]);

  const send = useCallback((msg: object) => {
    wsRef.current?.send(JSON.stringify(msg));
  }, []);

  return { connected, send };
}
