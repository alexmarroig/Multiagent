'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { AGENT_COLOR, type AgentNodeData } from '@/types/agentos';
import { NodeStatusBadge } from '@/components/agentos/NodeStatusBadge';

type Props = NodeProps<AgentNodeData>;

/**
 * Nó visual customizado para representar um agente no canvas.
 */
function AgentNode({ selected, data }: Props) {
  const borderColor = AGENT_COLOR[data.category];

  return (
    <div
      className="relative min-w-[240px] max-w-[280px] overflow-hidden rounded-xl border bg-white shadow-md dark:bg-slate-900"
      style={{
        borderColor,
        borderWidth: selected ? 3 : 2,
      }}
    >
      <Handle type="target" position={Position.Left} />

      <div className="absolute right-1 top-1 z-10">
        <NodeStatusBadge status={data.status ?? 'idle'} />
      </div>

      <div className="px-3 py-2 text-white" style={{ backgroundColor: borderColor }}>
        <p className="text-sm font-semibold">{data.label}</p>
      </div>
      <div className="space-y-2 p-3 text-xs text-slate-700 dark:text-slate-200">
        <p>{data.description}</p>
        <p>
          <span className="font-semibold">Modelo:</span> {data.model}
        </p>
        <p className="line-clamp-2">
          <span className="font-semibold">Prompt:</span> {data.prompt}
        </p>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default memo(AgentNode);
