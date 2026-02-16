'use client';

import { useMemo } from 'react';
import { AGENT_COLOR, AGENT_TEMPLATES, type AgentCategory } from '@/types/agentos';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const CATEGORY_LABEL: Record<AgentCategory, string> = {
  financial: 'Financeiro',
  marketing: 'Marketing',
  phone: 'Telefone',
  excel: 'Excel',
  travel: 'Turismo',
  supervisor: 'Supervisor',
  utility: 'Utilitários',
};

export default function AgentSidebar() {
  const addNodeFromTemplate = useCanvasStore((s) => s.addNodeFromTemplate);

  const grouped = useMemo(() => {
    const map = new Map<AgentCategory, typeof AGENT_TEMPLATES>();

    AGENT_TEMPLATES.forEach((template) => {
      const list = map.get(template.category) ?? [];
      list.push(template);
      map.set(template.category, list);
    });

    return Array.from(map.entries());
  }, []);

  return (
    <aside className="h-full w-80 border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-1 text-lg font-bold text-slate-900 dark:text-slate-100">Biblioteca de Agentes</h2>
      <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
        Clique em um agente para adicionar no canvas.
      </p>

      <div className="space-y-4 overflow-auto pr-1">
        {grouped.map(([category, templates]) => (
          <section key={category} className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {CATEGORY_LABEL[category]}
            </p>
            {templates.map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => addNodeFromTemplate(template)}
                className="w-full rounded-lg border border-slate-200 bg-white p-3 text-left transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:hover:bg-slate-800"
              >
                <div className="mb-1 flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: AGENT_COLOR[template.category] }}
                  />
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {template.name}
                  </p>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-300">{template.description}</p>
              </button>
            ))}
          </section>
import { AGENT_TEMPLATES } from '@/types/agentos';
import { useCanvasStore } from '@/hooks/useCanvasStore';

export default function AgentSidebar() {
  const addNodeFromTemplate = useCanvasStore((s) => s.addNodeFromTemplate);

  return (
    <aside className="h-full w-72 border-r bg-white p-4">
      <h2 className="mb-1 text-lg font-bold">Biblioteca de Agentes</h2>
      <p className="mb-4 text-xs text-slate-500">
        Clique em um item para adicionar no canvas.
      </p>

      <div className="space-y-2 overflow-auto">
        {AGENT_TEMPLATES.map((template) => (
          <button
            key={template.id}
            type="button"
            onClick={() => addNodeFromTemplate(template)}
            className="w-full rounded-lg border p-3 text-left hover:bg-slate-50"
          >
            <p className="text-sm font-semibold">{template.name}</p>
            <p className="text-xs text-slate-600">{template.description}</p>
          </button>
        ))}
      </div>
    </aside>
  );
}
