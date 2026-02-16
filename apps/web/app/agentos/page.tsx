'use client';

import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import ExecutionConsole from '@/components/agentos/ExecutionConsole';

/**
 * Página do Módulo 1 do AgentOS: canvas visual com drag-and-drop de agentes.
 */
export default function AgentOSPage() {
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
