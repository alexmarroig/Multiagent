'use client';

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-xl p-4">
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto border border-white/10 bg-black p-8 shadow-[0_0_50px_rgba(0,0,0,0.5)] custom-scrollbar"
      >
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-2xl font-black tracking-tighter text-white uppercase italic">Mission_Briefing</h3>
            <p className="text-[10px] font-mono text-cyber-cyan/60 uppercase tracking-widest mt-1">
              Ready_for_Deployment: {nodes.length} Agent(s)
            </p>
          </div>
          <button onClick={onClose} className="text-neutral-500 hover:text-white transition-colors font-mono text-xs">
            [ CLOSE_TERMINAL ]
          </button>
        </div>

        <div className="space-y-6">
          {toolNormalizationWarnings.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="border-l-2 border-amber-500 bg-amber-500/5 p-4 text-[11px] text-amber-200 font-mono"
            >
              <p className="font-bold mb-2">WARNING: UNMAPPED_TOOLS_DETECTED</p>
              <ul className="space-y-1 opacity-80">
                {toolNormalizationWarnings.map((warning) => (
                  <li key={warning.label}>
                    &gt; {warning.label}: {warning.unmapped.join(', ')}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          <div>
            <label className="block text-[10px] font-black text-neutral-500 uppercase tracking-[0.2em] mb-3">
              PRIMARY_OBJECTIVE_SPECIFICATION
            </label>
            <textarea
              value={objective}
              onChange={(event) => setObjective(event.target.value)}
              className="h-32 w-full border border-white/10 bg-white/5 p-4 text-xs text-white placeholder:text-neutral-700 outline-none focus:border-cyber-cyan transition-colors font-mono"
              placeholder="Ex: Analyze financial data and generate a report..."
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {agentsPresent.travel && (
              <>
                <input className="input-cyber" placeholder="destination" onChange={(e) => handleInputChange('destination', e.target.value)} />
                <input className="input-cyber" placeholder="checkin (YYYY-MM-DD)" onChange={(e) => handleInputChange('checkin', e.target.value)} />
                <input className="input-cyber" placeholder="checkout (YYYY-MM-DD)" onChange={(e) => handleInputChange('checkout', e.target.value)} />
                <input className="input-cyber" placeholder="budget_brl" onChange={(e) => handleInputChange('budget_brl', e.target.value)} />
              </>
            )}

            {agentsPresent.phone && (
              <input className="input-cyber col-span-full" placeholder="phone_number" onChange={(e) => handleInputChange('phone_number', e.target.value)} />
            )}

            {agentsPresent.financial && (
              <>
                <input className="input-cyber" placeholder="tickers (PETR4.SA,AAPL)" onChange={(e) => handleInputChange('tickers', e.target.value)} />
                <input className="input-cyber" placeholder="period (1y)" onChange={(e) => handleInputChange('period', e.target.value)} />
              </>
            )}
          </div>
        </div>

        <div className="mt-10 flex justify-end gap-4">
          <button type="button" onClick={onClose} className="btn-cyber-outline !px-6 !py-2 !text-xs !border-white/10 text-white/50">
            ABORT_MISSION
          </button>
          <button
            type="button"
            disabled={!objective.trim()}
            onClick={handleSubmit}
            className="btn-cyber-primary !px-10 !py-2 !text-xs"
          >
            INITIALIZE_DEPLOYMENT
          </button>
        </div>
      </motion.div>

      <style jsx global>{`
        .input-cyber {
          @apply w-full border border-white/10 bg-white/5 p-3 text-xs text-white placeholder:text-neutral-700 outline-none focus:border-cyber-cyan transition-colors font-mono;
        }
      `}</style>
    </div>
  );
}
