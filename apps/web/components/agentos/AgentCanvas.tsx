'use client';

import 'reactflow/dist/style.css';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import AgentNode from '@/components/agentos/AgentNode';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const nodeTypes = {
  agentNode: AgentNode,
};

type AgentCanvasProps = {
  onRun: () => void;
  isRunning: boolean;
};

export default function AgentCanvas({ onRun, isRunning }: AgentCanvasProps) {
export default function AgentCanvas() {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const onNodesChange = useCanvasStore((s) => s.onNodesChange);
  const onEdgesChange = useCanvasStore((s) => s.onEdgesChange);
  const onConnect = useCanvasStore((s) => s.onConnect);
  const selectNode = useCanvasStore((s) => s.selectNode);

  return (
    <main className="relative h-full w-full bg-slate-100 dark:bg-slate-950">
      <div className="absolute right-3 top-3 z-10">
        <button
          type="button"
          onClick={onRun}
          disabled={isRunning}
          className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isRunning ? 'Executando...' : 'Run'}
        </button>
      </div>

    <main className="h-full w-full bg-slate-100">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(_, node) => selectNode(node.id)}
        onPaneClick={() => selectNode(null)}
      >
        <MiniMap
          zoomable
          pannable
          style={{ background: 'transparent' }}
          maskColor="rgba(15, 23, 42, 0.15)"
        />
        <Controls className="!shadow-md" />
        <Background gap={20} size={1} className="!bg-slate-100 dark:!bg-slate-950" />
        <MiniMap zoomable pannable />
        <Controls />
        <Background gap={20} size={1} />
      </ReactFlow>
    </main>
  );
}
