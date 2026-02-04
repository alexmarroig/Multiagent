'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Node,
  Edge,
  Connection,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { supabase } from '@/lib/supabase';

const initialNodes: Node[] = [
  {
    id: 'node_1',
    type: 'default',
    data: { label: 'Start CEO Agent' },
    position: { x: 250, y: 5 },
  },
];

const AGENT_TYPES = [
  { type: 'ceo', label: 'CEO Agent', color: '#bfdbfe' },
  { type: 'cto', label: 'CTO Agent', color: '#bbf7d0' },
  { type: 'programmer', label: 'Programmer Agent', color: '#fef08a' },
  { type: 'reviewer', label: 'Reviewer Agent', color: '#fecaca' },
  { type: 'cpo', label: 'CPO (Artifacts)', color: '#ddd6fe' },
];

interface WorkflowEditorProps {
  projectId: string;
}

const WorkflowEditorInner = ({ projectId }: WorkflowEditorProps) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadWorkflow() {
      const { data } = await supabase
        .from('workflows')
        .select('*')
        .eq('project_id', projectId)
        .single();

      if (data) {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      }
    }
    loadWorkflow();
  }, [projectId]);

  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const data = JSON.parse(event.dataTransfer.getData('application/reactflow'));

      if (!reactFlowBounds || !reactFlowInstance) return;

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: `node_${Date.now()}`,
        type: 'default',
        position,
        data: { label: data.label },
        style: { background: data.color, borderRadius: '8px' },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance]
  );

  const saveWorkflow = async () => {
    setSaving(true);
    const { error } = await supabase.from('workflows').upsert({
      project_id: projectId,
      nodes: nodes,
      edges: edges,
    }, { onConflict: 'project_id' });

    if (error) alert(error.message);
    else alert('Workflow saved successfully!');
    setSaving(false);
  };

  return (
    <div className="flex h-[700px] border rounded-lg overflow-hidden bg-white">
      <aside className="w-64 border-r p-4 bg-gray-50">
        <h3 className="font-bold mb-4 text-sm uppercase text-gray-500">Agent Nodes</h3>
        <div className="space-y-2">
          {AGENT_TYPES.map((agent) => (
            <div
              key={agent.type}
              className="p-3 bg-white border rounded cursor-move hover:shadow-md transition text-sm font-medium"
              onDragStart={(event) => {
                event.dataTransfer.setData('application/reactflow', JSON.stringify(agent));
                event.dataTransfer.effectAllowed = 'move';
              }}
              draggable
            >
              {agent.label}
            </div>
          ))}
        </div>
        <p className="mt-6 text-xs text-gray-400">Drag and drop agents onto the canvas to build your automated team.</p>
      </aside>

      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
        >
          <Background />
          <Controls />
          <Panel position="top-right">
            <button
              onClick={saveWorkflow}
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-2 rounded shadow font-bold hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Workflow'}
            </button>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
};

export default function WorkflowEditor(props: WorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <WorkflowEditorInner {...props} />
    </ReactFlowProvider>
  );
}
