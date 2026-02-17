'use client';

import { useEffect, useRef, useState } from 'react';

export type EventType = 'thinking' | 'action' | 'tool_call' | 'result' | 'error' | 'done';

export interface AgentEvent {
  session_id: string;
  agent_id: string;
  agent_name: string;
  event_type: EventType;
  content: string;
  timestamp: string;
}

export function useAgentStream(sessionId: string | null) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    setEvents([]);
    setIsDone(false);
    setError(null);

    const base = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000';
    const ws = new WebSocket(`${base}/ws/${sessionId}`);

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = ({ data }) => {
      const parsed = JSON.parse(data) as Omit<AgentEvent, 'content'> & { content: unknown };
      const ev: AgentEvent = { ...parsed, content: typeof parsed.content === 'string' ? parsed.content : JSON.stringify(parsed.content) };
      setEvents((prev) => [...prev, ev]);
      if (ev.event_type === 'done') {
        setIsDone(true);
        setIsConnected(false);
      }
      if (ev.event_type === 'error') {
        setError(ev.content);
        setIsDone(true);
        setIsConnected(false);
      }
    };
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => {
      setIsConnected(false);
      setError('Conexão perdida');
    };
    wsRef.current = ws;

    return () => ws.close();
  }, [sessionId]);

  return { events, isConnected, isDone, error };
}
