'use client';

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
