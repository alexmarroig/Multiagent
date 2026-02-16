'use client';

import { useEffect, useState } from 'react';

export type AgentEvent = {
  session_id: string;
  agent_id: string;
  agent_name: string;
  event_type: string;
  content: unknown;
  timestamp: string;
};

export function useAgentStream(sessionId: string | null) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!sessionId) return;

    // Limpa os eventos ao iniciar uma nova sessão.
    setEvents([]);

    const wsBase = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000';
    const ws = new WebSocket(`${wsBase}/ws/${sessionId}`);

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      try {
        setEvents((prev) => [...prev, JSON.parse(event.data) as AgentEvent]);
      } catch {
        // Ignora payload inválido sem quebrar a UI.
      }
    };
    ws.onclose = () => setIsConnected(false);

    return () => ws.close();
  }, [sessionId]);

  return { events, isConnected };
}
