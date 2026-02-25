'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCanvasStore } from '@/hooks/useCanvasStore';

type Props = {
  onClose: () => void;
};

export default function LoadFlowModal({ onClose }: Props) {
  const [flows, setFlows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const listFlows = useCanvasStore((s) => s.listFlows);
  const loadFlow = useCanvasStore((s) => s.loadFlow);
  const lang = useCanvasStore((s) => s.language);

  useEffect(() => {
    listFlows()
      .then((res) => setFlows(res))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [listFlows]);

  const handleSelect = async (flowId: string) => {
    setLoading(true);
    try {
      await loadFlow(flowId);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const t = {
    en: {
      title: 'RESTORE_NEURAL_FLOW',
      subtitle: 'SELECT_DEPLOYMENT_ID',
      empty: 'NO_FLOWS_FOUND',
      cancel: 'ABORT',
      restore: 'RESTORE'
    },
    pt: {
      title: 'RESTAURAR_FLUXO_NEURAL',
      subtitle: 'SELECIONE_ID_DA_IMPLANTAÇÃO',
      empty: 'NENHUM_FLUXO_ENCONTRADO',
      cancel: 'ABORTAR',
      restore: 'RESTAURAR'
    }
  }[lang];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="glass-panel-elevated w-full max-w-2xl p-8 relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 h-2 w-2 border-t border-l border-cyber-cyan" />
        <div className="absolute bottom-0 right-0 h-2 w-2 border-b border-r border-cyber-cyan" />

        <div className="mb-8 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-black text-white tracking-tighter uppercase italic">
              {t.title}
            </h3>
            <p className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest mt-1">
              {t.subtitle}
            </p>
          </div>
          <button
            type="button"
            className="btn-cyber-outline !px-3 !py-1 !text-[10px]"
            onClick={onClose}
          >
            {t.cancel}
          </button>
        </div>

        <div className="max-h-[50vh] overflow-y-auto pr-4 custom-scrollbar">
          {loading ? (
            <div className="py-12 flex flex-col items-center gap-4">
              <div className="h-8 w-8 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
              <p className="text-[10px] font-mono text-cyber-cyan animate-pulse">SYNCHRONIZING...</p>
            </div>
          ) : flows.length === 0 ? (
            <div className="py-12 text-center text-[10px] font-mono text-neutral-600 uppercase">
              {t.empty}
            </div>
          ) : (
            <div className="space-y-4">
              {flows.map((flow) => (
                <motion.button
                  key={flow.id}
                  whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)', borderColor: 'rgba(0, 243, 255, 0.3)' }}
                  onClick={() => handleSelect(flow.id)}
                  className="w-full text-left border border-white/5 bg-white/[0.02] p-4 group transition-all"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-sm font-black text-white group-hover:text-cyber-cyan transition-colors uppercase italic">
                      {flow.name}
                    </h4>
                    <span className="text-[8px] font-mono text-neutral-600">
                      {new Date(flow.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-[10px] font-mono text-neutral-500 line-clamp-1">
                    {flow.description || 'No description available.'}
                  </p>
                </motion.button>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
