'use client';

import type { NodeStatus } from '@/types/agentos';

type Props = {
  status: NodeStatus;
};

export function NodeStatusBadge({ status }: Props) {
  if (status === 'idle') return (
    <span className="inline-flex items-center gap-1 border border-white/10 bg-black/40 px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest text-neutral-600">
      IDLE_STANDBY
    </span>
  );

  if (status === 'running') {
    return (
      <span className="inline-flex items-center gap-1 border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest text-amber-400">
        <span className="h-1.5 w-1.5 animate-pulse bg-amber-500" />
        PROCESSING
      </span>
    );
  }

  if (status === 'done') {
    return (
      <span className="inline-flex items-center gap-1 border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest text-emerald-400">
        READY
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest text-red-400">
      CRITICAL_FAIL
    </span>
  );
}
