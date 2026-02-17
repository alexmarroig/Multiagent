'use client';

import type { NodeStatus } from '@/types/agentos';

type Props = {
  status: NodeStatus;
};

export function NodeStatusBadge({ status }: Props) {
  if (status === 'idle') return null;

  if (status === 'running') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
        <span className="inline-block h-2 w-2 animate-spin rounded-full border border-amber-300 border-t-transparent" />
        Executando
      </span>
    );
  }

  if (status === 'done') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
        ✓ Concluído
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] font-semibold text-red-300">
      ✗ Erro
    </span>
  );
}
