'use client';

import 'reactflow/dist/style.css';
import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactFlow, { Background, Controls, MiniMap, type ReactFlowInstance } from 'reactflow';
import { AGENT_TEMPLATES } from '@/types/agentos';
import AgentNode from '@/components/agentos/AgentNode';
import ExecutionConsole from '@/components/agentos/ExecutionConsole';
import RunModal from '@/components/agentos/RunModal';
import TemplateGallery from '@/components/agentos/TemplateGallery';
import { useAgentStream } from '@/hooks/useAgentStream';
import { useCanvasStore } from '@/hooks/useCanvasStore';
import type { NodeStatus } from '@/types/agentos';

const nodeTypes = { agentNode: AgentNode };

function mapEventToStatus(eventType: string): NodeStatus | null {
  switch (eventType) {
    case 'thinking':
    case 'action':
    case 'tool_call':
      return 'running';
    case 'result':
      return 'done';
    case 'error':
      return 'error';
    default:
      return null;
  }
}

export default function AgentCanvas() {
  const [showRunModal, setShowRunModal] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);

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
  const addNodeFromTemplate = useCanvasStore((s) => s.addNodeFromTemplate);
  const reLayout = useCanvasStore((s) => s.reLayout);
  const lang = useCanvasStore((s) => s.language);

  const { events, isConnected, isDone, error } = useAgentStream(sessionId);

  const onDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const onDrop = (event: React.DragEvent) => {
    event.preventDefault();

    const templateId = event.dataTransfer.getData('application/reactflow');
    if (!templateId || !rfInstance) return;

    const template = AGENT_TEMPLATES.find((t) => t.id === templateId);
    if (!template) return;

    const position = rfInstance.screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    addNodeFromTemplate(template, position);
  };

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

  const runButtonText = runState === 'running'
    ? (lang === 'en' ? 'INITIALIZING...' : 'INICIALIZANDO...')
    : runState === 'done'
      ? (lang === 'en' ? 'RE_INITIALIZE' : 'REINICIALIZAR')
      : (lang === 'en' ? 'RUN_MISSION' : 'INICIAR_MISSÃO');

  return (
    <main className="relative flex h-full w-full flex-col bg-black overflow-hidden">
      {/* HUD Controls */}
      <div className="absolute right-6 top-6 z-10 flex flex-col items-end gap-3">
        <div className="flex gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="button"
            onClick={() => reLayout()}
            className="btn-cyber-outline !px-3 !py-1.5 !text-[9px] !border-white/20 !text-white/70"
          >
            {lang === 'en' ? 'AUTO_LAYOUT' : 'LAYOUT_AUTO'}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="button"
            onClick={() => setShowTemplates(true)}
            className="btn-cyber-outline !px-3 !py-1.5 !text-[9px] !border-white/20 !text-white/70"
          >
            MISSION_TEMPLATES
          </motion.button>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="button"
          onClick={() => setShowRunModal(true)}
          disabled={nodes.length === 0 || runState === 'running'}
          className={`btn-cyber-primary !px-8 !py-3 !text-[11px] ${
            runState === 'running' ? 'animate-pulse !bg-amber-500 !text-black' :
            runState === 'done' ? '!bg-cyber-magenta !text-white' : ''
          }`}
        >
          {runButtonText}
        </motion.button>
      </div>

      <div className="absolute left-6 top-6 z-10 pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="flex flex-col gap-1">
            <div className="h-0.5 w-8 bg-cyber-cyan shadow-[0_0_5px_#00f3ff]" />
            <div className="h-0.5 w-4 bg-cyber-cyan/50" />
          </div>
          <span className="font-mono text-[10px] tracking-[0.3em] text-cyber-cyan/60 uppercase">
            ORCHESTRATION_CANVAS_V4
          </span>
        </div>
      </div>

      <div className="min-h-0 flex-1 relative">
        <ReactFlow
          nodes={flowNodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          onInit={setRfInstance}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodeClick={(_, node) => selectNode(node.id)}
          onPaneClick={() => selectNode(null)}
        >
          <MiniMap
            zoomable
            pannable
            nodeColor="#00f3ff"
            nodeStrokeWidth={3}
          />
          <Controls className="!bg-black/50 !border-white/10 !fill-white" />
          <Background gap={40} size={1} color="rgba(0, 243, 255, 0.05)" />
        </ReactFlow>

        <div className="absolute inset-0 pointer-events-none border-[1px] border-white/5 m-4" />
      </div>

      <ExecutionConsole events={events} isConnected={isConnected} isDone={isDone} error={error} />

      <AnimatePresence>
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
      </AnimatePresence>

      <AnimatePresence>
        {showTemplates && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 overflow-auto bg-black/80 backdrop-blur-sm p-4 flex items-center justify-center"
          >
            <div className="w-full max-w-5xl">
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
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
