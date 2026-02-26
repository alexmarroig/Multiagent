'use client';

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const inputClassName =
  'mt-1 w-full border border-white/10 bg-white/5 p-3 text-xs text-white placeholder:text-neutral-700 outline-none focus:border-cyber-cyan transition-colors font-mono';

export default function AgentConfig() {
  const nodes = useCanvasStore((s) => s.nodes);
  const selectedNodeId = useCanvasStore((s) => s.selectedNodeId);
  const updateNodeData = useCanvasStore((s) => s.updateNodeData);
  const lang = useCanvasStore((s) => s.language);
  const [activeTab, setActiveTab] = useState<'core' | 'prompt'>('core');

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId),
    [nodes, selectedNodeId],
  );

  return (
    <motion.aside
      initial={{ x: 320 }}
      animate={{ x: 0 }}
      className="h-full w-80 border-l border-white/10 bg-black/40 backdrop-blur-xl p-4 flex flex-col"
    >
      <AnimatePresence mode="wait">
        {!selectedNode ? (
          <motion.div
            key="none"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex flex-col items-center justify-center h-full text-center p-6"
          >
            <div className="h-12 w-12 border border-dashed border-white/20 rounded-full flex items-center justify-center mb-4">
              <div className="h-2 w-2 bg-white/20 rounded-full animate-pulse" />
            </div>
            <h2 className="text-xs font-black tracking-widest text-white/40 uppercase mb-2">
               {lang === 'en' ? 'AWAITING_SELECTION' : 'AGUARDANDO_SELEÇÃO'}
            </h2>
            <p className="text-[10px] font-mono text-neutral-600 leading-relaxed uppercase">
              {lang === 'en' ? 'Click_on_a_node_to_access_core_parameters' : 'Clique_em_um_nó_para_acessar_parâmetros'}
            </p>
          </motion.div>
        ) : (
          <motion.div
            key={selectedNode.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-4 w-1 bg-cyber-magenta shadow-[0_0_8px_#ff00ff]" />
                <h2 className="text-sm font-black tracking-[0.2em] text-white uppercase">NODE_PARAMS</h2>
              </div>
              <p className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
                ID: {selectedNode.id}
              </p>
            </div>

            <div className="flex border-b border-white/10 mb-6">
              <button
                onClick={() => setActiveTab('core')}
                className={`flex-1 py-2 text-[10px] font-bold tracking-widest uppercase transition-all ${
                  activeTab === 'core' ? 'text-cyber-magenta border-b-2 border-cyber-magenta' : 'text-neutral-500 hover:text-neutral-300'
                }`}
              >
                {lang === 'en' ? 'CORE_SPECS' : 'ESPEC_CORE'}
              </button>
              <button
                onClick={() => setActiveTab('prompt')}
                className={`flex-1 py-2 text-[10px] font-bold tracking-widest uppercase transition-all ${
                  activeTab === 'prompt' ? 'text-cyber-magenta border-b-2 border-cyber-magenta' : 'text-neutral-500 hover:text-neutral-300'
                }`}
              >
                {lang === 'en' ? 'LOGIC_PROMPT' : 'PROMPT_LOGICA'}
              </button>
            </div>

            <AnimatePresence mode="wait">
              {activeTab === 'core' ? (
                <motion.div
                  key="core"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="space-y-4"
                >
                  <label className="block">
                    <span className="block text-[11px] font-black text-neutral-400 uppercase tracking-[0.2em] mb-2">
                       {lang === 'en' ? 'DESIGNATION' : 'DESIGNAÇÃO'}
                    </span>
                    <input
                      className={inputClassName}
                      value={selectedNode.data.label}
                      onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                    />
                  </label>

                  <label className="block">
                    <span className="block text-[11px] font-black text-neutral-400 uppercase tracking-[0.2em] mb-2">
                       {lang === 'en' ? 'CORE_ENGINE' : 'MOTOR_PRINCIPAL'}
                    </span>
                    <input
                      className={inputClassName}
                      value={selectedNode.data.model}
                      onChange={(e) => updateNodeData(selectedNode.id, { model: e.target.value })}
                    />
                  </label>

                  <label className="block">
                    <span className="block text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-1">
                       {lang === 'en' ? 'EQUIPPED_TOOLS (CSV)' : 'FERRAMENTAS_EQUIPADAS (CSV)'}
                    </span>
                    <textarea
                      className={`${inputClassName} h-24 resize-none`}
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
                </motion.div>
              ) : (
                <motion.div
                  key="prompt"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="space-y-4"
                >
                  <label className="block">
                    <span className="block text-[11px] font-black text-neutral-400 uppercase tracking-[0.2em] mb-2">
                       {lang === 'en' ? 'DIRECTIVE_PROMPT' : 'PROMPT_DE_DIRETIVA'}
                    </span>
                    <textarea
                      className={`${inputClassName} h-[400px] custom-scrollbar resize-none font-sans font-medium text-[13px] leading-relaxed p-4`}
                      value={selectedNode.data.prompt}
                      onChange={(e) => updateNodeData(selectedNode.id, { prompt: e.target.value })}
                    />
                    <div className="mt-2 text-[9px] font-mono text-neutral-600 flex justify-between">
                      <span>TOKENS: ~{Math.ceil(selectedNode.data.prompt.length / 4)}</span>
                      <span>UTF-8_SYNCED</span>
                    </div>
                  </label>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-auto pt-6 border-t border-white/5">
        <div className="flex justify-between items-center mb-2">
           <span className="text-[8px] text-neutral-700 font-mono">ENCRYPTION_STATUS</span>
           <span className="text-[8px] text-cyber-cyan font-mono">VERIFIED</span>
        </div>
        <div className="h-1 w-full bg-white/5">
           <div className="h-full w-full bg-cyber-cyan/20" />
        </div>
      </div>
    </motion.aside>
  );
}
