'use client';

import 'reactflow/dist/style.css';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import AgentNode from '@/components/agentos/AgentNode';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const nodeTypes = { agentNode: AgentNode };

export default function AgentCanvas() {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const onNodesChange = useCanvasStore((s) => s.onNodesChange);
  const onEdgesChange = useCanvasStore((s) => s.onEdgesChange);
  const onConnect = useCanvasStore((s) => s.onConnect);
  const selectNode = useCanvasStore((s) => s.selectNode);

  return (
    <main className="h-full w-full bg-slate-100 dark:bg-slate-950">
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
        <MiniMap zoomable pannable />
        <Controls />
        <Background gap={20} size={1} />
      </ReactFlow>
    </main>
  );
}
