'use client';

import { create } from 'zustand';
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from 'reactflow';
import { AGENT_TEMPLATES, type AgentNodeData, type AgentTemplate, type NodeStatus, type RunState } from '@/types/agentos';
import { supabase } from '@/lib/supabase/client';

type CanvasStore = {
  nodes: Node<AgentNodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  executionLogs: string[];
  sessionId: string | null;
  runState: RunState;
  nodeStatuses: Record<string, NodeStatus>;
  lastResult: string | null;
  backendOnline: boolean;
  language: 'en' | 'pt';
  setLanguage: (lang: 'en' | 'pt') => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNodeFromTemplate: (template: AgentTemplate, position?: { x: number; y: number }) => void;
  selectNode: (id: string | null) => void;
  updateNodeData: (id: string, data: Partial<AgentNodeData>) => void;
  appendLog: (line: string) => void;
  clearLogs: () => void;
  setSessionId: (id: string | null) => void;
  setRunState: (state: RunState) => void;
  setNodeStatus: (nodeId: string, status: NodeStatus) => void;
  setLastResult: (result: string) => void;
  setBackendOnline: (value: boolean) => void;
  resetRun: () => void;
  reLayout: () => void;
  saveFlow: (name: string, description?: string) => Promise<unknown>;
  loadFlow: (flowId: string) => Promise<void>;
  listFlows: () => Promise<any[]>;
};

const defaultNodes: Node<AgentNodeData>[] = [
  {
    id: 'node-supervisor',
    type: 'agentNode',
    position: { x: 450, y: 220 },
    data: {
      label: 'SupervisorAgent',
      category: 'supervisor',
      description: 'Coordena a execução dos agentes do fluxo.',
      model: 'gpt-4o-mini',
      prompt: AGENT_TEMPLATES.find((t) => t.id === 'supervisor-agent')?.defaultPrompt ?? '',
      tools: ['langgraph', 'evaluation'],
      status: 'idle',
    },
  },
];

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  nodes: defaultNodes,
  edges: [],
  selectedNodeId: defaultNodes[0]?.id ?? null,
  executionLogs: [
    '[BOOT] AGENT_OS_CANVAS_INITIALIZED',
    '[HINT] DRAG_PROTOCOLS_FROM_SIDEBAR_TO_START',
  ],
  sessionId: null,
  runState: 'idle',
  nodeStatuses: {},
  lastResult: null,
  backendOnline: false,
  language: 'pt',

  setLanguage: (language) => set({ language }),
  onNodesChange: (changes) => set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) })),
  onEdgesChange: (changes) => set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),
  onConnect: (connection) =>
    set((state) => ({
      edges: addEdge({
        ...connection,
        animated: true,
        style: { stroke: 'rgba(0, 243, 255, 0.4)', strokeWidth: 1.5 }
      }, state.edges),
    })),

  addNodeFromTemplate: (template, position) =>
    set((state) => {
      const id = `node-${template.id}-${Date.now()}`;
      const count = state.nodes.length;

      const newNode: Node<AgentNodeData> = {
        id,
        type: 'agentNode',
        position: position || { x: 160 + (count % 3) * 280, y: 110 + Math.floor(count / 3) * 180 },
        data: {
          label: template.name,
          category: template.category,
          description: template.description,
          model: 'gpt-4o-mini',
          prompt: template.defaultPrompt,
          tools: template.defaultTools,
          status: 'idle',
        },
      };

      const newNodes = [...state.nodes, newNode];

      // Auto-connect to Supervisor if it exists and this is not the supervisor itself
      let newEdges = [...state.edges];
      if (template.category !== 'supervisor') {
        const supervisor = state.nodes.find(n => n.data.category === 'supervisor');
        if (supervisor) {
          newEdges = addEdge({
            id: `edge-${supervisor.id}-${id}`,
            source: supervisor.id,
            target: id,
            animated: true,
            style: { stroke: 'rgba(0, 243, 255, 0.4)', strokeWidth: 1.5 }
          }, newEdges);
        }
      }

      return {
        nodes: newNodes,
        edges: newEdges,
        selectedNodeId: id,
      };
    }),

  selectNode: (id) => set({ selectedNodeId: id }),
  updateNodeData: (id, data) =>
    set((state) => ({
      nodes: state.nodes.map((node) => (node.id === id ? { ...node, data: { ...node.data, ...data } } : node)),
    })),
  appendLog: (line) => set((state) => ({ executionLogs: [...state.executionLogs, line] })),
  clearLogs: () => set({ executionLogs: ['[SYSTEM] LOGS_CLEARED'] }),
  setSessionId: (id) => set({ sessionId: id }),
  setRunState: (state) => set({ runState: state }),
  setNodeStatus: (nodeId, status) =>
    set((state) => ({ nodeStatuses: { ...state.nodeStatuses, [nodeId]: status } })),
  setLastResult: (result) => set({ lastResult: result }),
  setBackendOnline: (value) => set({ backendOnline: value }),
  resetRun: () => set({ sessionId: null, runState: 'idle', nodeStatuses: {}, lastResult: null }),

  reLayout: () => set((state) => {
    const supervisor = state.nodes.find(n => n.data.category === 'supervisor');
    const others = state.nodes.filter(n => n.data.category !== 'supervisor');

    const centerX = 450;
    const centerY = 220;
    const radius = 300;

    const newNodes = state.nodes.map(node => {
      if (node.data.category === 'supervisor') {
        return { ...node, position: { x: centerX, y: centerY } };
      }

      const idx = others.findIndex(n => n.id === node.id);
      const angle = (idx / others.length) * 2 * Math.PI;
      return {
        ...node,
        position: {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        }
      };
    });

    return { nodes: newNodes };
  }),

  saveFlow: async (name, description = '') => {
    const { nodes, edges } = get();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const config = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    };

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${apiBase}/api/flows`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
      body: JSON.stringify({ name, description, config }),
    });

    return response.json();
  },

  loadFlow: async (flowId) => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${apiBase}/api/flows/${flowId}`, {
      headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
    });

    const flow = await response.json();
    set({
      nodes: flow.config?.nodes ?? [],
      edges: flow.config?.edges ?? [],
      selectedNodeId: flow.config?.nodes?.[0]?.id ?? null,
    });
  },

  listFlows: async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${apiBase}/api/flows`, {
      headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
    });

    const data = await response.json();
    return data.flows || [];
  },
}));

export function findTemplateByAgentName(agentName: string): AgentTemplate | undefined {
  const normalized = agentName.toLowerCase();
  return AGENT_TEMPLATES.find((template) =>
    normalized.includes(template.name.toLowerCase().replace('agent', '')),
  );
}
