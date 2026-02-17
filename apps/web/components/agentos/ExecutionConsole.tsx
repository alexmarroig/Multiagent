'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { downloadExcel } from '@/lib/api';
import { downloadArtifactExcel, downloadExcel } from '@/lib/api';
import type { AgentEvent, EventType } from '@/hooks/useAgentStream';

type ExecutionConsoleProps = {
  events: AgentEvent[];
  isConnected: boolean;
  isDone: boolean;
  error: string | null;
};

type ArtifactPayload = {
  artifact_id?: string;
  artifact_path?: string;
};

const EVENT_STYLE: Record<EventType, { icon: string; badge: string; bg: string }> = {
  thinking: { icon: '🧠', badge: 'bg-amber-500/20 text-amber-300', bg: 'bg-amber-900/20' },
  action: { icon: '⚡', badge: 'bg-blue-500/20 text-blue-300', bg: 'bg-blue-900/20' },
  tool_call: { icon: '🔧', badge: 'bg-orange-500/20 text-orange-300', bg: 'bg-orange-900/20' },
  result: { icon: '✅', badge: 'bg-emerald-500/20 text-emerald-300', bg: 'bg-emerald-900/20' },
  error: { icon: '❌', badge: 'bg-red-500/20 text-red-300', bg: 'bg-red-900/20' },
  done: { icon: '🎉', badge: 'bg-white/20 text-white', bg: 'bg-slate-700/40' },
};

function relativeTime(isoDate: string): string {
  const diff = Math.max(0, Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000));
  if (diff < 60) return `há ${diff}s`;
  const minutes = Math.floor(diff / 60);
  return `há ${minutes}min`;
}

function parseArtifactEvent(event: AgentEvent): ArtifactPayload | null {
  if (event.event_type !== 'result') return null;
  const content = typeof event.content === 'string' ? event.content : '';
  if (!content) return null;

  try {
    const parsed = JSON.parse(content) as Record<string, unknown>;
    const artifactId = typeof parsed.artifact_id === 'string' ? parsed.artifact_id : undefined;
    const artifactPath = typeof parsed.artifact_path === 'string' ? parsed.artifact_path : undefined;
    const hasXlsx = (artifactId ?? artifactPath ?? '').toLowerCase().endsWith('.xlsx');
    return hasXlsx ? { artifact_id: artifactId, artifact_path: artifactPath } : null;
  } catch {
    return null;
  }
}

export default function ExecutionConsole({ events, isConnected, isDone, error }: ExecutionConsoleProps) {
  const [hiddenUntil, setHiddenUntil] = useState(0);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [events]);

  const visibleEvents = useMemo(
    () => events.filter((event) => new Date(event.timestamp).getTime() >= hiddenUntil),
    [events, hiddenUntil],
  );

  const excelMentioned = visibleEvents.some((event) => event.content.includes('.xlsx'));
  const latestExcelArtifact = useMemo(() => {
    for (let idx = visibleEvents.length - 1; idx >= 0; idx -= 1) {
      const artifact = parseArtifactEvent(visibleEvents[idx]);
      if (artifact) return artifact;
    }
    return null;
  }, [visibleEvents]);

  const excelMentioned = Boolean(
    latestExcelArtifact || visibleEvents.some((event) => String(event.content).toLowerCase().includes('.xlsx')),
  );

  const copyAll = async () => {
    const text = visibleEvents
      .map((event) => `[${event.event_type}] ${event.agent_name} (${event.timestamp}) ${event.content}`)
      .join('\n');
    await navigator.clipboard.writeText(text);
  };

  const downloadExcelFromResult = async () => {
    if (latestExcelArtifact) {
      await downloadArtifactExcel(latestExcelArtifact);
      return;
    }

    await downloadExcel({
      title: 'Resultado AgentOS',
      data: visibleEvents.map((event) => ({
        tipo: event.event_type,
        agente: event.agent_name,
        conteudo: event.content,
        timestamp: event.timestamp,
      })),
      filename: 'agentos-eventos.xlsx',
    });
  };

  return (
    <section className="h-72 border-t border-slate-700 bg-slate-950 p-3 font-mono text-xs text-green-300">
      <div className="mb-2 flex items-center justify-between border-b border-slate-700 pb-2">
        <div className="flex items-center gap-2">
          <p className="font-semibold uppercase text-slate-300">Execution Console</p>
          {isConnected && <span className="animate-pulse text-emerald-400">● Executando</span>}
          {!isConnected && isDone && !error && <span className="text-emerald-400">✓ Concluído</span>}
          {error && <span className="text-red-400">✗ Erro</span>}
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setHiddenUntil(Date.now())} className="rounded bg-slate-700 px-2 py-1 text-white hover:bg-slate-600">
            Limpar
          </button>
          <button type="button" onClick={copyAll} className="rounded bg-slate-700 px-2 py-1 text-white hover:bg-slate-600">
            Copiar tudo
          </button>
          {excelMentioned && (
            <button type="button" onClick={downloadExcelFromResult} className="rounded bg-emerald-700 px-2 py-1 text-white hover:bg-emerald-600">
              Download Excel
            </button>
          )}
        </div>
      </div>

      <div ref={listRef} className="h-56 space-y-2 overflow-auto pr-2">
        {visibleEvents.map((event, index) => {
          const style = EVENT_STYLE[event.event_type];
          return (
            <article key={`${event.timestamp}-${index}`} className={`rounded-md p-2 ${style.bg}`}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span>{style.icon}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${style.badge}`}>
                    {event.event_type}
                  </span>
                  <strong className="text-slate-100">{event.agent_name}</strong>
                </div>
                <span className="text-[10px] text-slate-400">{relativeTime(event.timestamp)}</span>
              </div>
              <p className={`whitespace-pre-wrap text-xs ${event.event_type === 'result' ? 'font-semibold text-emerald-200' : 'text-slate-200'}`}>
                {event.content}
                {String(event.content)}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
