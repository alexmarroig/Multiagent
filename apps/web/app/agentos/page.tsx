'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import TemplateGallery from '@/components/agentos/TemplateGallery';
import { healthCheck } from '@/lib/api';
import { useCanvasStore } from '@/hooks/useCanvasStore';
import { useAuth } from '@/hooks/useAuth';

export default function AgentOSPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [showTemplateTab, setShowTemplateTab] = useState(false);
  const backendOnline = useCanvasStore((s) => s.backendOnline);
  const setBackendOnline = useCanvasStore((s) => s.setBackendOnline);
  const saveFlow = useCanvasStore((s) => s.saveFlow);
  const { profile, signOut } = useAuth();

  useEffect(() => {
    healthCheck().then((isOnline) => setBackendOnline(isOnline));
  }, [setBackendOnline]);

  async function handleSave() {
    const name = window.prompt('Nome do fluxo:');
    if (!name) return;
    await saveFlow(name);
  }

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="flex h-screen flex-col bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
          <div>
            <h1 className="text-lg font-bold">AgentOS Canvas</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Módulo 4 • Auth + Dashboard + Save/Load</p>
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setShowTemplateTab((prev) => !prev)}
              className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white"
            >
              Templates
            </button>
            <button onClick={handleSave} className="rounded bg-green-600 px-3 py-1.5 text-sm font-semibold text-white">
              💾 Salvar
            </button>
            <button
              type="button"
              onClick={() => setDarkMode((prev) => !prev)}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold dark:border-slate-700"
            >
              {darkMode ? 'Light' : 'Dark'}
            </button>

            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-medium">
                  {profile?.full_name?.charAt(0) || profile?.email?.charAt(0) || 'U'}
                </div>
                <span className="text-sm font-medium hidden md:block">{profile?.full_name || profile?.email}</span>
              </button>

              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <div className="py-1">
                  <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                    {profile?.email}
                  </div>
                  {profile?.role === 'admin' && (
                    <Link href="/admin" className="block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700">
                      🛠️ Admin Dashboard
                    </Link>
                  )}
                  <Link href="/debug" className="block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700">
                    🐛 Debug
                  </Link>
                  <button
                    onClick={signOut}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Sair
                  </button>
                </div>
              </div>
            </div>
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
