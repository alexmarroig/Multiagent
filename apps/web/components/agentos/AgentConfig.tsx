'use client';

import { useMemo } from 'react';
import { useCanvasStore } from '@/hooks/useCanvasStore';

export default function AgentConfig() {
  const nodes = useCanvasStore((s) => s.nodes);
  const selectedNodeId = useCanvasStore((s) => s.selectedNodeId);
  const updateNodeData = useCanvasStore((s) => s.updateNodeData);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId),
    [nodes, selectedNodeId],
  );

  if (!selectedNode) {
    return (
      <aside className="h-full w-80 border-l bg-white p-4">
        <h2 className="text-lg font-bold">Configuração</h2>
        <p className="mt-2 text-sm text-slate-500">
          Selecione um nó para editar prompt, modelo e ferramentas.
        </p>
      </aside>
    );
  }

  return (
    <aside className="h-full w-80 border-l bg-white p-4">
      <h2 className="mb-4 text-lg font-bold">Configuração do Agente</h2>

      <div className="space-y-3">
        <label className="block text-sm font-medium">
          Nome
          <input
            className="mt-1 w-full rounded border p-2 text-sm"
            value={selectedNode.data.label}
            onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
          />
        </label>

        <label className="block text-sm font-medium">
          Modelo
          <input
            className="mt-1 w-full rounded border p-2 text-sm"
            value={selectedNode.data.model}
            onChange={(e) => updateNodeData(selectedNode.id, { model: e.target.value })}
          />
        </label>

        <label className="block text-sm font-medium">
          Prompt
          <textarea
            className="mt-1 h-32 w-full rounded border p-2 text-sm"
            value={selectedNode.data.prompt}
            onChange={(e) => updateNodeData(selectedNode.id, { prompt: e.target.value })}
          />
        </label>

        <label className="block text-sm font-medium">
          Ferramentas (CSV)
          <input
            className="mt-1 w-full rounded border p-2 text-sm"
            value={selectedNode.data.tools.join(', ')}
            onChange={(e) =>
              updateNodeData(selectedNode.id, {
                tools: e.target.value
                  .split(',')
                  .map((item) => item.trim())
                  .filter(Boolean),
              })
            }
          />
        </label>
      </div>
    </aside>
  );
}
