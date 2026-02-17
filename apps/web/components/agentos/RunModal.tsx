'use client';

import { useMemo, useState } from 'react';
import { normalizeToolIds } from '@/shared/tool_ids';
import type { Node } from 'reactflow';
import { runFlow, type FlowPayload } from '@/lib/api';
import { useCanvasStore } from '@/hooks/useCanvasStore';
import type { AgentNodeData } from '@/types/agentos';

type RunModalProps = {
  nodes: Node<AgentNodeData>[];
  edges: { id: string; source: string; target: string }[];
  onClose: () => void;
  onRun: (sessionId: string) => void;
};

const TOOL_ALIASES: Record<string, string> = {
  yfinance: 'finance',
  openpyxl: 'excel',
  twilio: 'phone',
  tavily: 'search',
  playwright: 'browser',
  'google-calendar': 'calendar',
};

function normalizeTools(tools: string[]): string[] {
  return tools.map((tool) => TOOL_ALIASES[tool] ?? tool).filter((tool, idx, arr) => arr.indexOf(tool) === idx);
}

function mapCategoryToAgentType(category: string, label: string): string {
  if (category === 'utility') {
    return label.toLowerCase().includes('meeting') ? 'meeting' : 'supervisor';
  }
  return category;
}

export default function RunModal({ nodes, edges, onClose, onRun }: RunModalProps) {
  const [objective, setObjective] = useState('');
  const [extraInputs, setExtraInputs] = useState<Record<string, string>>({});
  const setRunState = useCanvasStore((s) => s.setRunState);
  const resetRun = useCanvasStore((s) => s.resetRun);

  const agentsPresent = useMemo(() => {
    const labels = nodes.map((n) => n.data.label.toLowerCase());
    const categories = new Set(nodes.map((n) => n.data.category));
    return {
      travel: categories.has('travel') || labels.some((l) => l.includes('travel')),
      phone: categories.has('phone') || labels.some((l) => l.includes('phone')),
      meeting: labels.some((l) => l.includes('meeting')),
      marketing: categories.has('marketing') || labels.some((l) => l.includes('marketing')),
      financial: categories.has('financial') || labels.some((l) => l.includes('financial')),
    };
  }, [nodes]);

  const handleInputChange = (key: string, value: string) => {
    setExtraInputs((prev) => ({ ...prev, [key]: value }));
  };

  const toolNormalizationWarnings = useMemo(() => {
    return nodes
      .map((node) => ({ label: node.data.label, ...normalizeToolIds(node.data.tools) }))
      .filter((node) => node.unmapped.length > 0);
  }, [nodes]);

  const handleSubmit = async () => {
    if (!objective.trim()) return;

    try {
      resetRun();
      setRunState('running');

      const payload: FlowPayload = {
        session_id: '',
        nodes: nodes.map((node) => ({
          id: node.id,
          agent_type: mapCategoryToAgentType(node.data.category, node.data.label).toLowerCase(),
          label: node.data.label,
          model: node.data.model,
          provider: 'anthropic',
          system_prompt: node.data.prompt,
          tools: normalizeTools(node.data.tools),
          tools: normalizeToolIds(node.data.tools).normalized,
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
        })),
        inputs: {
          objetivo: objective,
          ...extraInputs,
        },
      };

      const result = await runFlow(payload);
      onRun(result.session_id);
      onClose();
    } catch {
      setRunState('error');
    }
  };

  return (
    <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
        <h3 className="text-xl font-bold">Executar fluxo</h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {nodes.length} agente(s) prontos para executar.
        </p>

        <div className="mt-4 space-y-4">
        {toolNormalizationWarnings.length > 0 && (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
            <p className="font-semibold">Algumas tools não puderam ser mapeadas e serão ignoradas:</p>
            <ul className="mt-1 list-disc pl-5">
              {toolNormalizationWarnings.map((warning) => (
                <li key={warning.label}>
                  <span className="font-medium">{warning.label}</span>: {warning.unmapped.join(', ')}
                </li>
              ))}
            </ul>
          </div>
        )}

          <label className="block text-sm font-medium">
            Descreva o objetivo dos agentes
            <textarea
              value={objective}
              onChange={(event) => setObjective(event.target.value)}
              className="mt-1 h-28 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950"
              placeholder="Ex: Monte roteiro Paris 5 dias com orçamento de R$8.000"
            />
          </label>

          {agentsPresent.travel && (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="destination" onChange={(e) => handleInputChange('destination', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="checkin (YYYY-MM-DD)" onChange={(e) => handleInputChange('checkin', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="checkout (YYYY-MM-DD)" onChange={(e) => handleInputChange('checkout', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="budget_brl" onChange={(e) => handleInputChange('budget_brl', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="adults" onChange={(e) => handleInputChange('adults', e.target.value)} />
            </div>
          )}

          {agentsPresent.phone && (
            <input className="w-full rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="phone_number" onChange={(e) => handleInputChange('phone_number', e.target.value)} />
          )}

          {agentsPresent.meeting && (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="date (YYYY-MM-DD)" onChange={(e) => handleInputChange('date', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="attendees (a@x.com,b@y.com)" onChange={(e) => handleInputChange('attendees', e.target.value)} />
            </div>
          )}

          {agentsPresent.marketing && (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="product" onChange={(e) => handleInputChange('product', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="audience" onChange={(e) => handleInputChange('audience', e.target.value)} />
            </div>
          )}

          {agentsPresent.financial && (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="tickers (PETR4.SA,AAPL)" onChange={(e) => handleInputChange('tickers', e.target.value)} />
              <input className="rounded border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-950" placeholder="period (1y)" onChange={(e) => handleInputChange('period', e.target.value)} />
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded border border-slate-300 px-4 py-2 text-sm dark:border-slate-600">
            Cancelar
          </button>
          <button
            type="button"
            disabled={!objective.trim()}
            onClick={handleSubmit}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            Executar Fluxo
          </button>
        </div>
      </div>
    </div>
  );
}
