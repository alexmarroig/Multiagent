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

    const wsBase = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000';
    const ws = new WebSocket(`${wsBase}/ws/${sessionId}`);

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = ({ data }) => {
      try {
        const parsed = JSON.parse(data) as Omit<AgentEvent, 'content'> & { content: unknown };
        const content = typeof parsed.content === 'string' ? parsed.content : JSON.stringify(parsed.content);
        const event: AgentEvent = { ...parsed, content };
        setEvents((prev) => [...prev, event]);

        if (event.event_type === 'done') {
          setIsDone(true);
          setIsConnected(false);
        }
        if (event.event_type === 'error') {
          setError(content);
          setIsDone(true);
          setIsConnected(false);
        }
      } catch {
        // Ignora payload inválido sem quebrar a UI.
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
