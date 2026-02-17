'use client';

import { useEffect, useState } from 'react';
import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import TemplateGallery from '@/components/agentos/TemplateGallery';
import { healthCheck } from '@/lib/api';
import { useCanvasStore } from '@/hooks/useCanvasStore';

/**
 * Página do Módulo 3: conexão real com backend + templates + execução completa.
 */
export default function AgentOSPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [showTemplateTab, setShowTemplateTab] = useState(false);
  const backendOnline = useCanvasStore((s) => s.backendOnline);
  const setBackendOnline = useCanvasStore((s) => s.setBackendOnline);

  useEffect(() => {
    healthCheck().then((isOnline) => setBackendOnline(isOnline));
  }, [setBackendOnline]);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="flex h-screen flex-col bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
          <div>
            <h1 className="text-lg font-bold">AgentOS Canvas</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Módulo 3 • Fluxo real com templates e execução em tempo real
            </p>
          </div>
          <div className="space-x-2">
            <button
              type="button"
              onClick={() => setShowTemplateTab((prev) => !prev)}
              className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white"
            >
              Templates
            </button>
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
          </div>
        </header>

        {!backendOnline && (
          <div className="border-b border-amber-500/30 bg-amber-500/20 px-4 py-2 text-sm text-amber-200">
            Backend offline — inicie com docker-compose up
          </div>
        )}

        {showTemplateTab && (
          <div className="border-b border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
            <TemplateGallery onTemplateApplied={() => setShowTemplateTab(false)} />
          </div>
        )}

        <div className="flex min-h-0 flex-1">
          <AgentSidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1">
              <AgentCanvas />
            </div>
          </div>
          <AgentConfig />
        </div>
      </div>
    </div>
  );
}
