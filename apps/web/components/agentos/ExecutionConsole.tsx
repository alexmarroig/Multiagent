'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { downloadArtifactExcel, downloadExcel } from '@/lib/api';
import type { AgentEvent, EventType } from '@/hooks/useAgentStream';
import { useCanvasStore } from '@/hooks/useCanvasStore';

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

const EVENT_STYLE: Record<EventType, { icon: string; color: string; bg: string }> = {
  thinking: { icon: '[THINK]', color: 'text-amber-400', bg: 'bg-amber-400/5' },
  action: { icon: '[EXEC ]', color: 'text-cyber-cyan', bg: 'bg-cyber-cyan/5' },
  tool_call: { icon: '[TOOL ]', color: 'text-cyber-magenta', bg: 'bg-cyber-magenta/5' },
  result: { icon: '[RES  ]', color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  error: { icon: '[FAIL ]', color: 'text-red-400', bg: 'bg-red-400/10' },
  done: { icon: '[DONE ]', color: 'text-white', bg: 'bg-white/10' },
};

function relativeTime(isoDate: string): string {
  const diff = Math.max(0, Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000));
  if (diff < 60) return `${diff}s`;
  const minutes = Math.floor(diff / 60);
  return `${minutes}m`;
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
  const lang = useCanvasStore((s) => s.language);

  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [events]);

  const visibleEvents = useMemo(
    () => events.filter((event) => new Date(event.timestamp).getTime() >= hiddenUntil),
    [events, hiddenUntil],
  );

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

  const t = {
    en: {
      title: 'SYSTEM_LOG_CORE',
      streaming: 'STREAMING_ACTIVE',
      done: 'SESSION_TERMINATED_SUCCESSFULLY',
      fail: 'CRITICAL_SYSTEM_ERROR',
      clear: 'CLEAR',
      copy: 'COPY_LOG',
      export: 'EXPORT_XLSX'
    },
    pt: {
      title: 'LOG_CENTRAL_DO_SISTEMA',
      streaming: 'STREAMING_ATIVO',
      done: 'SESSÃO_TERMINADA_COM_SUCESSO',
      fail: 'ERRO_CRÍTICO_DO_SISTEMA',
      clear: 'LIMPAR',
      copy: 'COPIAR_LOG',
      export: 'EXPORTAR_XLSX'
    }
  }[lang];

  return (
    <motion.section
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="h-72 border-t border-white/10 bg-black/60 backdrop-blur-md p-3 font-mono text-[10px]"
    >
      <div className="mb-2 flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center gap-4">
          <p className="font-black uppercase tracking-widest text-white/40">{t.title}</p>
          <div className="flex items-center gap-2">
            {isConnected && (
              <span className="flex items-center gap-1.5 text-cyber-cyan">
                <span className="h-1 w-1 rounded-full bg-cyber-cyan animate-pulse" />
                {t.streaming}
              </span>
            )}
            {!isConnected && isDone && !error && (
              <span className="text-emerald-400">{t.done}</span>
            )}
            {error && <span className="text-red-400">{t.fail}</span>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setHiddenUntil(Date.now())} className="btn-cyber-outline !px-2 !py-1 !text-[9px] !border-white/10 hover:!border-white/30 text-white/50">
            {t.clear}
          </button>
          <button type="button" onClick={copyAll} className="btn-cyber-outline !px-2 !py-1 !text-[9px] !border-white/10 hover:!border-white/30 text-white/50">
            {t.copy}
          </button>
          {excelMentioned && (
            <button type="button" onClick={downloadExcelFromResult} className="btn-cyber-primary !px-3 !py-1 !text-[9px] !bg-emerald-500 !text-black">
              EXPORT_XLSX
            </button>
          )}
        </div>
      </div>

      <div ref={listRef} className="h-56 overflow-auto pr-2 custom-scrollbar">
        <AnimatePresence initial={false}>
          {visibleEvents.map((event, index) => {
            const style = EVENT_STYLE[event.event_type];
            return (
              <motion.article
                key={`${event.timestamp}-${index}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`mb-1 p-2 border-l border-white/5 ${style.bg} hover:bg-white/[0.05] transition-colors group`}
              >
                <div className="flex items-start gap-3">
                  <span className={`font-bold shrink-0 ${style.color}`}>{style.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white font-bold">{event.agent_name}</span>
                      <span className="text-[8px] text-neutral-600">@ {relativeTime(event.timestamp)}</span>
                    </div>
                    <p className={`whitespace-pre-wrap leading-relaxed ${event.event_type === 'result' ? 'text-emerald-300 font-bold' : 'text-neutral-400'}`}>
                      {event.content}
                    </p>
                  </div>
                </div>
              </motion.article>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.section>
  );
}
