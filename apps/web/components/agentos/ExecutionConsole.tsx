'use client';

import { useCanvasStore } from '@/hooks/useCanvasStore';

export default function ExecutionConsole() {
  const executionLogs = useCanvasStore((s) => s.executionLogs);
  const appendLog = useCanvasStore((s) => s.appendLog);
  const clearLogs = useCanvasStore((s) => s.clearLogs);

  const handleMockRun = () => {
    appendLog(`[run] Fluxo disparado em ${new Date().toLocaleTimeString('pt-BR')}.`);
    appendLog('[supervisor] Delegando tarefas para agentes conectados...');
    appendLog('[status] Módulo 1 concluído: fluxo visual pronto para integração backend.');
  };

  return (
    <section className="h-56 border-t bg-slate-950 p-3 font-mono text-xs text-green-300">
      <div className="mb-2 flex items-center justify-between border-b border-slate-700 pb-2">
        <p className="font-semibold uppercase text-slate-300">Execution Console</p>
        <div className="space-x-2">
          <button
            type="button"
            onClick={handleMockRun}
            className="rounded bg-emerald-600 px-2 py-1 text-white hover:bg-emerald-500"
          >
            Run Mock
          </button>
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
