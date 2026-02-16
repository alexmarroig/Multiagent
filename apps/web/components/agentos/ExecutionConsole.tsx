'use client';

import { useCanvasStore } from '@/hooks/useCanvasStore';

type ExecutionConsoleProps = {
  isConnected?: boolean;
};

export default function ExecutionConsole({ isConnected = false }: ExecutionConsoleProps) {
  const executionLogs = useCanvasStore((s) => s.executionLogs);
  const clearLogs = useCanvasStore((s) => s.clearLogs);

  return (
    <section className="h-56 border-t border-slate-700 bg-slate-950 p-3 font-mono text-xs text-green-300">
      <div className="mb-2 flex items-center justify-between border-b border-slate-700 pb-2">
        <p className="font-semibold uppercase text-slate-300">Execution Console</p>
        <div className="flex items-center gap-3">
          <span className={`text-[10px] ${isConnected ? 'text-emerald-400' : 'text-amber-400'}`}>
            {isConnected ? 'WS conectado' : 'WS desconectado'}
          </span>
          <button
            type="button"
            onClick={clearLogs}
            className="rounded bg-slate-700 px-2 py-1 text-white hover:bg-slate-600"
          >
            Limpar
          </button>
        </div>
      </div>
      <div className="h-44 overflow-auto pr-2">
        {executionLogs.map((line, idx) => (
          <p key={`${line}-${idx}`}>{line}</p>
        ))}
      </div>
    </section>
  );
}
