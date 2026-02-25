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
  const [view, setView] = useState<'logs' | 'metrics'>('logs');
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

  const metrics = useMemo(() => {
    if (!events.length) return null;
    const start = new Date(events[0].timestamp).getTime();
    const end = isDone ? new Date(events[events.length - 1].timestamp).getTime() : Date.now();
    const duration = Math.max(0, (end - start) / 1000);

    const toolCalls = events.filter(e => e.event_type === 'tool_call').length;
    const uniqueAgents = new Set(events.map(e => e.agent_id)).size;
    const errors = events.filter(e => e.event_type === 'error').length;

    // Mock token calculation: roughly 4 chars per token
    const totalChars = events.reduce((acc, e) => acc + (typeof e.content === 'string' ? e.content.length : 0), 0);
    const estTokens = Math.floor(totalChars / 4);

    return {
      duration: duration.toFixed(1),
      toolCalls,
      uniqueAgents,
      errors,
      estTokens,
      cost: (estTokens * 0.00001).toFixed(4) // Mock cost
    };
  }, [events, isDone]);

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
      export: 'EXPORT_XLSX',
      logs: 'LOGS',
      metrics: 'METRICS'
    },
    pt: {
      title: 'LOG_CENTRAL_DO_SISTEMA',
      streaming: 'STREAMING_ATIVO',
      done: 'SESSÃO_TERMINADA_COM_SUCESSO',
      fail: 'ERRO_CRÍTICO_DO_SISTEMA',
      clear: 'LIMPAR',
      copy: 'COPIAR_LOG',
      export: 'EXPORTAR_XLSX',
      logs: 'LOGS',
      metrics: 'MÉTRICAS'
    }
  }[lang];

  return (
    <motion.section
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="h-72 border-t border-white/10 bg-black/60 backdrop-blur-md p-3 font-mono text-[10px]"
    >
      <div className="mb-2 flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center gap-6">
          <div className="flex bg-white/5 p-0.5 border border-white/10">
            <button
              onClick={() => setView('logs')}
              className={`px-3 py-1 text-[9px] font-bold transition-all ${view === 'logs' ? 'bg-cyber-cyan text-black' : 'text-neutral-500 hover:text-white'}`}
            >
              {t.logs}
            </button>
            <button
              onClick={() => setView('metrics')}
              className={`px-3 py-1 text-[9px] font-bold transition-all ${view === 'metrics' ? 'bg-cyber-cyan text-black' : 'text-neutral-500 hover:text-white'}`}
            >
              {t.metrics}
            </button>
          </div>
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
        <AnimatePresence mode="wait">
          {view === 'metrics' ? (
            metrics ? (
            <motion.div
              key="metrics-view"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6"
            >
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">TOTAL_TIME</p>
                <p className="text-2xl font-black text-cyber-cyan">{metrics.duration}s</p>
              </div>
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">AGENTS_ENGAGED</p>
                <p className="text-2xl font-black text-white">{metrics.uniqueAgents}</p>
              </div>
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">TOOL_EXECUTIONS</p>
                <p className="text-2xl font-black text-cyber-magenta">{metrics.toolCalls}</p>
              </div>
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">FAILURES_DETECTED</p>
                <p className={`text-2xl font-black ${metrics.errors > 0 ? 'text-red-500' : 'text-emerald-500'}`}>{metrics.errors}</p>
              </div>
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">ESTIMATED_TOKENS</p>
                <p className="text-2xl font-black text-amber-500">{metrics.estTokens}</p>
              </div>
              <div className="glass-panel p-4 border-white/5">
                <p className="text-[9px] text-neutral-500 uppercase mb-1">MOCK_COST_EST</p>
                <p className="text-2xl font-black text-white">${metrics.cost}</p>
              </div>
            </motion.div>
            ) : (
              <motion.div
                key="no-metrics"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center text-neutral-700 font-mono"
              >
                <div className="h-12 w-12 border border-dashed border-white/10 rounded-full flex items-center justify-center mb-4">
                  <div className="h-2 w-2 bg-white/10 rounded-full animate-ping" />
                </div>
                <p className="text-[10px] tracking-widest uppercase">{lang === 'en' ? 'AWAITING_MISSION_TELEMETRY' : 'AGUARDANDO_TELEMETRIA_DA_MISSÃO'}</p>
              </motion.div>
            )
          ) : (
            visibleEvents.map((event, index) => {
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
          })
          )}
        </AnimatePresence>
      </div>
    </motion.section>
  );
}
