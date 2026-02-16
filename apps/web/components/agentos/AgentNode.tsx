'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { AGENT_COLOR, type AgentNodeData } from '@/types/agentos';

type Props = NodeProps<AgentNodeData>;

/**
 * Nó visual customizado para representar um agente no canvas.
 */
function AgentNode({ selected, data }: Props) {
  const borderColor = AGENT_COLOR[data.category];

  return (
    <div
      className="min-w-[240px] max-w-[280px] rounded-xl border bg-white shadow-md"
      style={{
        borderColor,
        borderWidth: selected ? 3 : 2,
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div
        className="rounded-t-xl px-3 py-2 text-white"
        style={{ backgroundColor: borderColor }}
      >
        <p className="text-sm font-semibold">{data.label}</p>
      </div>
      <div className="space-y-2 p-3 text-xs text-slate-700">
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
