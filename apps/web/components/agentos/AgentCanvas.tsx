'use client';

import 'reactflow/dist/style.css';
import { useEffect, useMemo, useState } from 'react';
import ReactFlow, { Background, Controls, MiniMap, type ReactFlowInstance } from 'reactflow';
import AgentNode from '@/components/agentos/AgentNode';
import ExecutionConsole from '@/components/agentos/ExecutionConsole';
import RunModal from '@/components/agentos/RunModal';
import TemplateGallery from '@/components/agentos/TemplateGallery';
import { useAgentStream } from '@/hooks/useAgentStream';
import { useCanvasStore } from '@/hooks/useCanvasStore';
import type { NodeStatus } from '@/types/agentos';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import AgentNode from '@/components/agentos/AgentNode';
import { useCanvasStore } from '@/hooks/useCanvasStore';

const nodeTypes = {
  agentNode: AgentNode,
};

function mapEventToStatus(eventType: string): NodeStatus | null {
  if (eventType === 'thinking' || eventType === 'action' || eventType === 'tool_call') return 'running';
  if (eventType === 'result') return 'done';
  if (eventType === 'error') return 'error';
  return null;
}

export default function AgentCanvas() {
  const [showRunModal, setShowRunModal] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);

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
  const sessionId = useCanvasStore((s) => s.sessionId);
  const runState = useCanvasStore((s) => s.runState);
  const nodeStatuses = useCanvasStore((s) => s.nodeStatuses);
  const setNodeStatus = useCanvasStore((s) => s.setNodeStatus);
  const setRunState = useCanvasStore((s) => s.setRunState);
  const setSessionId = useCanvasStore((s) => s.setSessionId);
  const setLastResult = useCanvasStore((s) => s.setLastResult);

  const { events, isConnected, isDone, error } = useAgentStream(sessionId);

  useEffect(() => {
    if (error) setRunState('error');
  }, [error, setRunState]);

  useEffect(() => {
    if (!events.length) return;

    events.forEach((event) => {
      const status = mapEventToStatus(event.event_type);
      if (status && event.agent_id) {
        setNodeStatus(event.agent_id, status);
      }
      if (event.event_type === 'result') {
        setLastResult(event.content);
      }
      if (event.event_type === 'done') {
        setRunState('done');
      }
    });
  }, [events, setLastResult, setNodeStatus, setRunState]);

  const flowNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          status: nodeStatuses[node.id] ?? 'idle',
        },
      })),
    [nodes, nodeStatuses],
  );

  const runButtonText = runState === 'running' ? 'Executando...' : runState === 'done' ? 'Executar novamente' : 'Run';
  const runButtonClass =
    runState === 'running'
      ? 'animate-pulse bg-amber-500'
      : runState === 'done'
        ? 'bg-emerald-700'
        : 'bg-emerald-600';

  return (
    <main className="relative flex h-full w-full flex-col bg-slate-100 dark:bg-slate-950">
      <div className="absolute right-3 top-3 z-10 flex gap-2">
        <button
          type="button"
          onClick={() => setShowTemplates(true)}
          className="rounded bg-slate-700 px-3 py-1.5 text-sm font-semibold text-white"
        >
          Templates
        </button>
        <button
          type="button"
          onClick={() => setShowRunModal(true)}
          disabled={nodes.length === 0 || runState === 'running'}
          className={`rounded px-3 py-1.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 ${runButtonClass}`}
        >
          {runButtonText}
        </button>
      </div>

      <div className="min-h-0 flex-1">
        <ReactFlow
          nodes={flowNodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          onInit={setRfInstance}
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
        </ReactFlow>
      </div>

      <ExecutionConsole events={events} isConnected={isConnected} isDone={isDone} error={error} />

      {showRunModal && (
        <RunModal
          nodes={nodes}
          edges={edges}
          onClose={() => setShowRunModal(false)}
          onRun={(newSessionId) => {
            setSessionId(newSessionId);
            setRunState('running');
            setShowRunModal(false);
          }}
        />
      )}

      {showTemplates && (
        <div className="absolute inset-0 z-20 overflow-auto bg-black/40 p-4">
          <TemplateGallery
            onClose={() => setShowTemplates(false)}
            onTemplateApplied={() => {
              setShowTemplates(false);
              setShowRunModal(true);
              setTimeout(() => {
                rfInstance?.fitView({ padding: 0.2, duration: 600 });
              }, 80);
            }}
          />
        </div>
      )}

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
