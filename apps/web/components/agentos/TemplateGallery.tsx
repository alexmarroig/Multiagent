'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
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
  calendar: 'meeting-agent',
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
  const lang = useCanvasStore((s) => s.language);

  useEffect(() => {
    fetchTemplates()
      .then((res) => setTemplates(res.templates))
      .catch(() => setTemplates([]));
  }, []);

  const fallbackTemplates = useMemo<Template[]>(
    () => [
      {
        id: 'travel_agency',
        name: 'PROTOCOL_VOYAGER',
        description: 'travel → financial → meeting',
        agents: ['travel', 'financial', 'meeting'],
        color: 'orange',
        inputs: ['destination', 'checkin', 'checkout', 'budget_brl'],
      },
      {
        id: 'marketing_company',
        name: 'PROTOCOL_GROWTH',
        description: 'marketing → financial → excel → phone',
        agents: ['marketing', 'financial', 'excel', 'phone'],
        color: 'blue',
        inputs: ['product', 'audience'],
      },
      {
        id: 'financial_office',
        name: 'PROTOCOL_WEALTH',
        description: 'financial → excel → supervisor',
        agents: ['financial', 'excel', 'supervisor'],
        color: 'green',
        inputs: ['tickers', 'period'],
      },
      {
        id: 'executive_assistant',
        name: 'PROTOCOL_COMMAND',
        description: 'meeting → phone → calendar → supervisor',
        agents: ['meeting', 'phone', 'calendar', 'supervisor'],
        color: 'purple',
        inputs: ['date', 'attendees', 'phone_number'],
      },
    ],
    [],
  );

  const source = templates.length ? templates : fallbackTemplates;

  const applyTemplate = (template: Template) => {
    const confirmMsg = lang === 'en' ? 'Clear canvas and apply new protocol?' : 'Limpar canvas e aplicar novo protocolo?';
    if (nodes.length > 0 && !window.confirm(confirmMsg)) {
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
          x: 120 + (index % 3) * 280,
          y: 120 + Math.floor(index / 3) * 250,
        },
        data: {
          label: agent.name,
          category: agent.category,
          description: agent.description,
          model: 'gpt-4o-mini',
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
      style: { stroke: 'rgba(0, 243, 255, 0.4)', strokeWidth: 1.5 },
    }));

    useCanvasStore.setState({
      nodes: generatedNodes,
      edges: generatedEdges,
      selectedNodeId: generatedNodes[0]?.id ?? null,
    });

    onTemplateApplied?.();
    onClose?.();
  };

  const t = {
    en: {
      title: 'Neural_Protocols',
      subtitle: 'Select_Deployment_Configuration',
      dismiss: '[ DISMISS ]',
      unsupported: 'UNSUPPORTED_AGENTS',
      inputs: 'INPUT_VARS',
      initialize: 'INITIALIZE'
    },
    pt: {
      title: 'Protocolos_Neurais',
      subtitle: 'Selecione_Configuracao_de_Implantacao',
      dismiss: '[ DESCARTAR ]',
      unsupported: 'AGENTES_NAO_SUPORTADOS',
      inputs: 'VARIAVEIS_ENTRADA',
      initialize: 'INICIALIZAR'
    }
  }[lang];

  return (
    <section className="glass-panel p-8 max-w-5xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
           <h3 className="text-2xl font-black tracking-tighter text-white uppercase italic">{t.title}</h3>
           <p className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest mt-1">{t.subtitle}</p>
        </div>
        {onClose && (
          <button
            type="button"
            className="btn-cyber-outline !px-3 !py-1 !text-[10px]"
            onClick={onClose}
          >
            {t.dismiss}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 max-h-[60vh] overflow-y-auto pr-4 custom-scrollbar">
        {source.map((template) => {
          const invalidAgents = template.agents.filter((agent) => !mapAgentNameToTemplate(agent));
          const isInvalid = invalidAgents.length > 0;

          return (
            <motion.article
              key={template.id}
              whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,0.03)' }}
              className="border border-white/5 bg-white/[0.01] p-6 transition-all group"
            >
              <div className="flex justify-between items-start mb-4">
                 <h4 className="text-lg font-black text-white tracking-tight italic group-hover:text-cyber-cyan transition-colors">{template.name}</h4>
                 <div className="h-1 w-8 bg-white/10" />
              </div>

              <p className="text-[11px] text-neutral-500 font-mono mb-4">{template.description}</p>

              <div className="flex flex-wrap gap-2 mb-6">
                {template.agents.map((agent) => (
                  <span
                    key={`${template.id}-${agent}`}
                    className="border border-white/10 bg-white/5 px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest text-neutral-400"
                  >
                    {agent}
                  </span>
                ))}
              </div>

              {isInvalid && (
                <p className="mb-4 text-[9px] text-red-400 font-mono uppercase">
                  {t.unsupported}: ({invalidAgents.join(', ')})
                </p>
              )}

              <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                <span className="text-[9px] text-neutral-600 font-mono uppercase">{t.inputs}: {template.inputs.length}</span>
                <button
                  type="button"
                  onClick={() => applyTemplate(template)}
                  disabled={isInvalid}
                  className="btn-cyber-primary !px-4 !py-1 !text-[10px]"
                >
                  {t.initialize}
                </button>
              </div>
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}
