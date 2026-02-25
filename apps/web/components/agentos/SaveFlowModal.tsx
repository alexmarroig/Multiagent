'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useCanvasStore } from '@/hooks/useCanvasStore';

type Props = {
  onClose: () => void;
};

export default function SaveFlowModal({ onClose }: Props) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const saveFlow = useCanvasStore((s) => s.saveFlow);
  const lang = useCanvasStore((s) => s.language);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    setLoading(true);
    try {
      await saveFlow(name, description);
      onClose();
    } catch (error) {
      console.error('Failed to save flow', error);
    } finally {
      setLoading(false);
    }
  };

  const t = {
    en: {
      title: 'SAVE_NEURAL_FLOW',
      name: 'DEPLOYMENT_NAME',
      desc: 'MISSION_DESCRIPTION',
      cancel: 'ABORT',
      save: 'EXECUTE_BACKUP'
    },
    pt: {
      title: 'SALVAR_FLUXO_NEURAL',
      name: 'NOME_DA_IMPLANTAÇÃO',
      desc: 'DESCRIÇÃO_DA_MISSÃO',
      cancel: 'ABORTAR',
      save: 'EXECUTAR_BACKUP'
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
        className="glass-panel-elevated w-full max-w-md p-8 relative"
      >
        <div className="absolute top-0 left-0 h-2 w-2 border-t border-l border-cyber-cyan" />
        <div className="absolute bottom-0 right-0 h-2 w-2 border-b border-r border-cyber-cyan" />

        <h3 className="text-xl font-black text-white tracking-tighter uppercase italic mb-6">
          {t.title}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">
              {t.name}
            </label>
            <input
              autoFocus
              className="w-full border border-white/10 bg-white/5 p-3 text-xs text-white outline-none focus:border-cyber-cyan font-mono"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: ALPHA_OMEGA_01"
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-2">
              {t.desc}
            </label>
            <textarea
              className="w-full border border-white/10 bg-white/5 p-3 text-xs text-white outline-none focus:border-cyber-cyan font-mono h-24 resize-none"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="..."
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-cyber-outline flex-1 !py-3 !text-[10px]"
            >
              {t.cancel}
            </button>
            <button
              type="submit"
              disabled={loading || !name}
              className="btn-cyber-primary flex-1 !py-3 !text-[10px]"
            >
              {loading ? '...' : t.save}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
