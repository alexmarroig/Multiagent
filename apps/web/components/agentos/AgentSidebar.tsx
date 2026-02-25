'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { AGENT_COLOR, AGENT_TEMPLATES, type AgentCategory } from '@/types/agentos';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const CATEGORY_LABEL: Record<string, Record<AgentCategory, string>> = {
  en: {
    financial: 'FINANCIAL_CORE',
    marketing: 'MARKETING_OPS',
    phone: 'VOIP_COMMS',
    excel: 'DATA_TABLES',
    travel: 'LOGISTICS',
    supervisor: 'CORE_ORCHESTRATOR',
    utility: 'SYSTEM_TOOLS',
  },
  pt: {
    financial: 'NUCLEO_FINANCEIRO',
    marketing: 'MARKETING_OPS',
    phone: 'COMUN_VOIP',
    excel: 'TABELAS_DADOS',
    travel: 'LOGISTICA',
    supervisor: 'ORQUESTRADOR_CORE',
    utility: 'FERRAMENTAS_SISTEMA',
  }
};

const containerVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { staggerChildren: 0.05, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: { opacity: 1, x: 0 }
};

export default function AgentSidebar() {
  const addNodeFromTemplate = useCanvasStore((s) => s.addNodeFromTemplate);
  const lang = useCanvasStore((s) => s.language);

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
    <motion.aside
      initial={{ x: -320 }}
      animate={{ x: 0 }}
      transition={{ type: 'spring', damping: 20, stiffness: 100 }}
      className="h-full w-80 border-r border-white/10 bg-black/40 backdrop-blur-xl p-4 flex flex-col"
    >
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-4 w-1 bg-cyber-cyan shadow-[0_0_8px_#00f3ff]" />
          <h2 className="text-sm font-black tracking-[0.2em] text-white uppercase">{lang === 'en' ? 'Neural_Library' : 'Biblioteca_Neural'}</h2>
        </div>
        <p className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
          {lang === 'en' ? 'Select_Protocol_to_Initialize' : 'Selecione_Protocolo_para_Iniciar'}
        </p>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="flex-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar"
      >
        {grouped.map(([category, templates]) => (
          <section key={category} className="space-y-3">
            <div className="flex items-center gap-3">
              <p className="text-[10px] font-bold tracking-widest text-cyber-cyan/60 whitespace-nowrap uppercase">
                {CATEGORY_LABEL[lang][category]}
              </p>
              <div className="h-px w-full bg-white/5" />
            </div>
            {templates.map((template) => (
              <motion.button
                key={template.id}
                variants={itemVariants}
                whileHover={{ x: 5, backgroundColor: 'rgba(255,255,255,0.05)', borderColor: 'rgba(0, 243, 255, 0.3)' }}
                whileTap={{ scale: 0.95, x: 10 }}
                onClick={() => addNodeFromTemplate(template)}
                className="group w-full border border-white/5 bg-white/[0.02] p-4 text-left transition-all hover:border-cyber-cyan/30"
              >
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-bold text-white group-hover:text-cyber-cyan transition-colors">
                    {template.name}
                  </p>
                  <span
                    className="h-1.5 w-1.5 rounded-full animate-pulse shadow-[0_0_5px_currentColor]"
                    style={{ color: AGENT_COLOR[template.category], backgroundColor: 'currentColor' }}
                  />
                </div>
                <p className="text-[10px] font-mono leading-relaxed text-neutral-500 group-hover:text-neutral-300">
                  {template.description}
                </p>
              </motion.button>
            ))}
          </section>
        ))}
      </motion.div>

      <div className="mt-4 pt-4 border-t border-white/5 font-mono text-[8px] text-neutral-700">
        SYSTEM_CAPACITY: 84% // NODES_ACTIVE: {AGENT_TEMPLATES.length}
      </div>
    </motion.aside>
  );
}
