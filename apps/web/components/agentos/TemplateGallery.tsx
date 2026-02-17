'use client';

import { useEffect, useMemo, useState } from 'react';
import type { Edge, Node } from 'reactflow';
import { AGENT_TEMPLATES, type AgentNodeData, type AgentTemplate } from '@/types/agentos';
import { fetchTemplates, type Template } from '@/lib/api';
import { useCanvasStore } from '@/hooks/useCanvasStore';

type TemplateGalleryProps = {
  onClose?: () => void;
  onTemplateApplied?: () => void;
};

const AGENT_ALIAS: Record<string, AgentTemplate['id']> = {
  financial: 'financial-analyst',
  travel: 'travel-agent',
  meeting: 'meeting-agent',
  phone: 'phone-agent',
  excel: 'excel-agent',
  marketing: 'marketing-agent',
  supervisor: 'supervisor-agent',
};

function mapAgentNameToTemplate(agentName: string): AgentTemplate | null {
  const normalized = agentName.toLowerCase().trim();
  const mappedId = AGENT_ALIAS[normalized];
  if (!mappedId) return null;
  return AGENT_TEMPLATES.find((t) => t.id === mappedId) ?? null;
}

export default function TemplateGallery({ onClose, onTemplateApplied }: TemplateGalleryProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const nodes = useCanvasStore((s) => s.nodes);

  useEffect(() => {
    fetchTemplates().then((res) => setTemplates(res.templates)).catch(() => setTemplates([]));
  }, []);

  const fallbackTemplates = useMemo<Template[]>(
    () => [
      {
        id: 'travel_agency',
        name: 'Agência de Turismo',
        description: 'travel → financial → meeting',
        agents: ['travel', 'financial', 'meeting'],
        color: 'orange',
        inputs: ['destination', 'checkin', 'checkout', 'budget_brl'],
      },
      {
        id: 'marketing_company',
        name: 'Empresa de Marketing',
        description: 'marketing → excel → phone → supervisor',
        agents: ['marketing', 'excel', 'phone', 'supervisor'],
        color: 'blue',
        inputs: ['product', 'audience'],
      },
      {
        id: 'financial_office',
        name: 'Escritório Financeiro',
        description: 'financial → excel → supervisor',
        agents: ['financial', 'excel', 'supervisor'],
        color: 'green',
        inputs: ['tickers', 'period'],
      },
      {
        id: 'executive_assistant',
        name: 'Assistente Executivo',
        description: 'meeting → phone → supervisor',
        agents: ['meeting', 'phone', 'supervisor'],
        color: 'purple',
        inputs: ['date', 'attendees', 'phone_number'],
      },
    ],
    [],
  );

  const source = templates.length ? templates : fallbackTemplates;

  const applyTemplate = (template: Template) => {
    if (nodes.length > 0 && !window.confirm('Limpar canvas atual e aplicar template?')) {
      return;
    }

    const mappedTemplates = template.agents.map(mapAgentNameToTemplate);
    if (mappedTemplates.some((item) => !item)) {
      return;
    }

    const generatedNodes: Node<AgentNodeData>[] = mappedTemplates.map((mapped, index) => {
      const agent = mapped as AgentTemplate;
      return {
        id: `tpl-${template.id}-${index}`,
        type: 'agentNode',
        position: {
          x: 120 + (index % 3) * 250,
          y: 120 + Math.floor(index / 3) * 180,
        },
        data: {
          label: agent.name,
          category: agent.category,
          description: agent.description,
          model: 'gpt-4.1-mini',
          prompt: agent.defaultPrompt,
          tools: agent.defaultTools,
          status: 'idle',
        },
      };
    });

    const generatedEdges: Edge[] = generatedNodes.slice(1).map((node, index) => ({
      id: `tpl-edge-${template.id}-${index}`,
      source: generatedNodes[index].id,
      target: node.id,
      animated: true,
      style: { strokeWidth: 2 },
    }));

    useCanvasStore.setState({
      nodes: generatedNodes,
      edges: generatedEdges,
      selectedNodeId: generatedNodes[0]?.id ?? null,
    });

    onTemplateApplied?.();
    onClose?.();
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold">Marketplace de Templates</h3>
        {onClose && (
          <button type="button" className="rounded border border-slate-300 px-3 py-1 text-sm dark:border-slate-600" onClick={onClose}>
            Fechar
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {source.map((template) => {
          const invalidAgents = template.agents.filter((agent) => !mapAgentNameToTemplate(agent));
          const isInvalid = invalidAgents.length > 0;

          return (
            <article key={template.id} className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-2xl">{template.color === 'orange' ? '🟠' : template.color === 'blue' ? '🔵' : template.color === 'green' ? '🟢' : '🟣'}</p>
              <h4 className="mt-2 text-base font-bold">{template.name}</h4>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{template.description}</p>
              <div className="mt-3 flex flex-wrap gap-1">
                {template.agents.map((agent) => (
                  <span key={`${template.id}-${agent}`} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase dark:bg-slate-800">
                    {agent}
                  </span>
                ))}
              </div>
              {isInvalid && (
                <p className="mt-2 text-xs text-red-400">Template inválido: agentes não suportados ({invalidAgents.join(', ')})</p>
              )}
              <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Inputs: {template.inputs.join(', ')}</p>
              <button
                type="button"
                onClick={() => applyTemplate(template)}
                disabled={isInvalid}
                className="mt-3 rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                Usar Template
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}
