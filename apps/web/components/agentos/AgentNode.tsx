'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { motion } from 'framer-motion';
import { AGENT_COLOR, type AgentNodeData } from '@/types/agentos';
import { NodeStatusBadge } from '@/components/agentos/NodeStatusBadge';
import { useCanvasStore } from '@/hooks/useCanvasStore';

type Props = NodeProps<AgentNodeData>;

function AgentNode({ selected, data }: Props) {
  const accentColor = AGENT_COLOR[data.category];
  const isRunning = data.status === 'running';
  const lang = useCanvasStore((s) => s.language);

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`relative min-w-[260px] max-w-[300px] overflow-hidden rounded-sm border-t-4 bg-black/90 backdrop-blur-md transition-all duration-300 ${
        selected ? 'shadow-[0_0_25px_rgba(255,255,255,0.15)] ring-1 ring-white/20' : ''
      }`}
      style={{
        borderTopColor: accentColor,
        borderColor: selected ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: accentColor, border: 'none', borderRadius: 0, width: 8, height: 8 }}
      />

      <div className="absolute right-2 top-2 z-10 scale-75 origin-top-right">
        <NodeStatusBadge status={data.status ?? 'idle'} />
      </div>

      <div className="px-5 py-4 border-b border-white/10 bg-white/[0.03]">
        <p className="text-[11px] font-mono tracking-widest text-neutral-400 uppercase mb-1.5">NODE_ID: {data.category}</p>
        <p className="text-base font-black text-white tracking-tight">{data.label}</p>
      </div>

      <div className="space-y-4 p-5 text-[12px] font-medium text-neutral-300">
        <p className="line-clamp-3 italic leading-relaxed text-neutral-400">&quot;{data.description}&quot;</p>

        <div className="grid grid-cols-2 gap-3 pt-2">
          <div className="bg-white/5 p-2 border border-white/10 rounded-sm">
            <span className="block text-[9px] text-neutral-500 font-bold uppercase mb-1">{lang === 'en' ? 'Engine' : 'Motor'}</span>
            <span className="text-white font-mono font-bold">{data.model.split('/')[1] || data.model}</span>
          </div>
          <div className="bg-white/5 p-2 border border-white/10 rounded-sm">
            <span className="block text-[9px] text-neutral-500 font-bold uppercase mb-1">{lang === 'en' ? 'Priority' : 'Prioridade'}</span>
            <span className="text-white font-mono font-bold text-cyber-cyan">{lang === 'en' ? 'HIGH' : 'ALTA'}</span>
          </div>
        </div>

        {isRunning && (
          <div className="mt-2">
            <div className="flex justify-between text-[8px] text-cyber-cyan mb-1">
              <span>{lang === 'en' ? 'PROCESSING' : 'PROCESSANDO'}</span>
              <span className="animate-pulse">{lang === 'en' ? 'ACTIVE_STREAM' : 'STREAM_ATIVO'}</span>
            </div>
            <div className="h-1 w-full bg-white/5 overflow-hidden">
              <motion.div
                animate={{ x: ['-100%', '100%'] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                className="h-full w-1/3 bg-cyber-cyan"
              />
            </div>
          </div>
        )}
      </div>

      {/* Decorative corner accents */}
      <div className="absolute bottom-0 right-0 h-4 w-4">
        <div className="absolute bottom-1 right-1 h-1 w-1 bg-white/20" />
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: accentColor, border: 'none', borderRadius: 0, width: 8, height: 8 }}
      />
    </motion.div>
  );
}

export default memo(AgentNode);
