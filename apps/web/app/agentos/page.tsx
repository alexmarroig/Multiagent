'use client';

import { useEffect, useMemo, useState } from 'react';
import { useState } from 'react';
import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import ExecutionConsole from '@/components/agentos/ExecutionConsole';
import { useAgentStream } from '@/hooks/useAgentStream';
import { useCanvasStore } from '@/hooks/useCanvasStore';

function mapCategoryToAgentType(category: string, label: string): string {
  if (category === 'utility') {
    return label.toLowerCase().includes('meeting') ? 'meeting' : 'supervisor';
  }
  return category;
}

/**
 * Página do Módulo 2: integra canvas com backend de execução + streaming.
 */
export default function AgentOSPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const appendLog = useCanvasStore((s) => s.appendLog);

  const { events, isConnected } = useAgentStream(sessionId);

  useEffect(() => {
    if (!events.length) return;
    const last = events[events.length - 1];
    const content =
      typeof last.content === 'string' ? last.content : JSON.stringify(last.content, null, 0);
    appendLog(`[${last.event_type}] ${last.agent_name}: ${content}`);
    if (last.event_type === 'done' || last.event_type === 'error') {
      setIsRunning(false);
    }
  }, [events, appendLog]);

  const flowConfig = useMemo(
    () => ({
      session_id: '',
      nodes: nodes.map((node) => ({
        id: node.id,
        agent_type: mapCategoryToAgentType(node.data.category, node.data.label),
        label: node.data.label,
        model: node.data.model,
        provider: 'anthropic',
        system_prompt: node.data.prompt,
        tools: node.data.tools,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      })),
      inputs: {
        objetivo: 'Executar fluxo criado no canvas AgentOS',
      },
    }),
    [nodes, edges],
  );

  const handleRun = async () => {
    try {
      setIsRunning(true);
      appendLog('[run] Enviando fluxo para o backend...');

      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/agents/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(flowConfig),
      });

      const data = (await response.json()) as { session_id: string; status: string };
      if (!response.ok) {
        throw new Error('Falha ao iniciar execução do fluxo.');
      }

      setSessionId(data.session_id);
      appendLog(`[run] Sessão ${data.session_id} iniciada (${data.status}).`);
    } catch (error) {
      appendLog(`[error] ${error instanceof Error ? error.message : 'Erro desconhecido.'}`);
      setIsRunning(false);
    }
  };

/**
 * Página do Módulo 1 do AgentOS: canvas visual com drag-and-drop de agentes.
 */
export default function AgentOSPage() {
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="flex h-screen flex-col bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
          <div>
            <h1 className="text-lg font-bold">AgentOS Canvas</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Módulo 2 • Canvas conectado ao backend com stream em tempo real
              Módulo 1 • Biblioteca por categoria + canvas + painel de configuração
            </p>
          </div>
          <div className="space-x-2">
            <button
              type="button"
              onClick={() => setDarkMode((prev) => !prev)}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold dark:border-slate-700"
            >
              {darkMode ? 'Light' : 'Dark'}
            </button>
            <button className="rounded bg-slate-900 px-3 py-1.5 text-sm font-semibold text-white dark:bg-slate-700">
              Save
            </button>
            <button className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white">
              Run
            </button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1">
          <AgentSidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1">
              <AgentCanvas onRun={handleRun} isRunning={isRunning} />
            </div>
            <ExecutionConsole isConnected={isConnected} />
          </div>
          <AgentConfig />
        </div>
              <AgentCanvas />
            </div>
            <ExecutionConsole />
          </div>
          <AgentConfig />
        </div>
  return (
    <div className="flex h-screen flex-col bg-slate-100">
      <header className="flex h-14 items-center justify-between border-b bg-white px-4">
        <div>
          <h1 className="text-lg font-bold">AgentOS Canvas</h1>
          <p className="text-xs text-slate-500">
            Módulo 1 • Biblioteca de agentes + canvas + painel de configuração
          </p>
        </div>
        <div className="space-x-2">
          <button className="rounded bg-slate-900 px-3 py-1.5 text-sm font-semibold text-white">
            Save
          </button>
          <button className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white">
            Run
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <AgentSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1">
            <AgentCanvas />
          </div>
          <ExecutionConsole />
        </div>
        <AgentConfig />
      </div>
    </div>
  );
}
