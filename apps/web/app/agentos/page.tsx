'use client';

import { useState } from 'react';
import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import ExecutionConsole from '@/components/agentos/ExecutionConsole';

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
              <AgentCanvas />
            </div>
            <ExecutionConsole />
          </div>
          <AgentConfig />
        </div>
      </div>
    </div>
  );
}
