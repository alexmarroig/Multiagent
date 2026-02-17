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

const SUPPORTED_AGENT_TYPES = ['financial', 'travel', 'meeting', 'phone', 'excel', 'marketing', 'supervisor'] as const;

const AGENT_ALIASES: Record<string, (typeof SUPPORTED_AGENT_TYPES)[number]> = {
  calendar: 'meeting',
};

type TemplateValidation = {
  invalidAgents: string[];
  normalizedAgents: string[];
  aliasWarnings: string[];
};

function mapAgentNameToTemplate(agentName: string): AgentTemplate | null {
  const normalized = agentName.toLowerCase();
  const exact = AGENT_TEMPLATES.find((t) => normalized.includes(t.name.toLowerCase().replace('agent', '')));
  return exact ?? null;
}

function validateTemplateAgents(template: Template): TemplateValidation {
  const invalidAgents: string[] = [];
  const normalizedAgents: string[] = [];
  const aliasWarnings: string[] = [];

  template.agents.forEach((agent) => {
    const normalized = agent.toLowerCase();
    const alias = AGENT_ALIASES[normalized];
    const resolved = alias ?? normalized;

    if (alias) {
      aliasWarnings.push(`Alias aplicado em ${template.id}: ${agent} -> ${alias}`);
    }

    if (SUPPORTED_AGENT_TYPES.includes(resolved as (typeof SUPPORTED_AGENT_TYPES)[number])) {
      normalizedAgents.push(resolved);
      return;
    }

    invalidAgents.push(agent);
  });

  return {
    invalidAgents,
    normalizedAgents,
    aliasWarnings,
  };
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
        description: 'marketing → financial → excel → phone',
        agents: ['marketing', 'financial', 'excel', 'phone'],
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
        description: 'meeting → phone → calendar → supervisor',
        agents: ['meeting', 'phone', 'calendar', 'supervisor'],
        color: 'purple',
        inputs: ['date', 'attendees', 'phone_number'],
      },
    ],
    [],
  );

  const source = templates.length ? templates : fallbackTemplates;
  const templateValidation = useMemo(() => {
    const validations = source.map((template) => ({
      template,
      validation: validateTemplateAgents(template),
    }));

    validations.forEach(({ validation }) => {
      validation.aliasWarnings.forEach((warning) => {
        console.warn(`[TemplateGallery] ${warning}`);
      });
    });

    return validations;
  }, [source]);

  const applyTemplate = (template: Template, normalizedAgents: string[]) => {
    if (nodes.length > 0 && !window.confirm('Limpar canvas atual e aplicar template?')) {
      return;
    }

    const generatedNodes: Node<AgentNodeData>[] = normalizedAgents.map((agent, index) => {
      const mapped = mapAgentNameToTemplate(agent);
      if (!mapped) {
        throw new Error(`Agente sem template mapeado: ${agent}`);
      }

      return {
        id: `tpl-${template.id}-${index}`,
        type: 'agentNode',
        position: {
          x: 120 + (index % 3) * 250,
          y: 120 + Math.floor(index / 3) * 180,
        },
        data: {
          label: mapped.name,
          category: mapped.category,
          description: mapped.description,
          model: 'gpt-4.1-mini',
          prompt: mapped.defaultPrompt,
          tools: mapped.defaultTools,
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
        {templateValidation.map(({ template, validation }) => (
          <article key={template.id} className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
            <p className="text-2xl">{template.color === 'orange' ? '🟠' : template.color === 'blue' ? '🔵' : template.color === 'green' ? '🟢' : '🟣'}</p>
            <h4 className="mt-2 text-base font-bold">{template.name}</h4>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{template.description}</p>
            {validation.invalidAgents.length > 0 && (
              <p className="mt-2 inline-flex rounded-full bg-rose-100 px-2 py-1 text-xs font-semibold text-rose-700 dark:bg-rose-900/40 dark:text-rose-300">
                Erro de template: agente desconhecido ({validation.invalidAgents.join(', ')})
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-1">
              {template.agents.map((agent) => (
                <span key={`${template.id}-${agent}`} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase dark:bg-slate-800">
                  {agent}
                </span>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Inputs: {template.inputs.join(', ')}</p>
            <button
              type="button"
              onClick={() => applyTemplate(template, validation.normalizedAgents)}
              disabled={validation.invalidAgents.length > 0}
              className="mt-3 rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              Usar Template
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
