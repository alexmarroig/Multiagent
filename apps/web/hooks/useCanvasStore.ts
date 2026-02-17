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
import {
  AGENT_TEMPLATES,
  type AgentNodeData,
  type AgentTemplate,
  type NodeStatus,
  type RunState,
} from '@/types/agentos';
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
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNodeFromTemplate: (template: AgentTemplate) => void;
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
  saveFlow: (name: string, description?: string) => Promise<unknown>;
  loadFlow: (flowId: string) => Promise<void>;
};

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  executionLogs: [
    '[boot] AgentOS canvas inicializado.',
    '[hint] Arraste agentes da sidebar para o canvas.',
  ],
  sessionId: null,
  runState: 'idle',
  nodeStatuses: {},
  lastResult: null,
  backendOnline: false,

  onNodesChange: (changes) =>
    set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) })),

  onEdgesChange: (changes) =>
    set((state) => ({ edges: applyEdgeChanges(changes, state.edges) })),

  onConnect: (connection) =>
    set((state) => ({
      edges: addEdge(
        {
          ...connection,
          animated: true,
          style: { strokeWidth: 2 },
        },
        state.edges,
      ),
    })),

  addNodeFromTemplate: (template) =>
    set((state) => {
      const id = `node-${template.id}-${Date.now()}`;
      const count = state.nodes.length;

      const node: Node<AgentNodeData> = {
        id,
        type: 'agentNode',
        position: {
          x: 160 + (count % 3) * 280,
          y: 110 + Math.floor(count / 3) * 180,
        },
        data: {
          label: template.name,
          category: template.category,
          description: template.description,
          model: 'gpt-4.1-mini',
          prompt: template.defaultPrompt,
          tools: template.defaultTools,
          status: 'idle',
        },
      };

      return {
        nodes: [...state.nodes, node],
        selectedNodeId: id,
        executionLogs: [
          ...state.executionLogs,
          `[canvas] Nó ${template.name} adicionado ao fluxo.`,
        ],
      };
    }),

  selectNode: (id) => set(() => ({ selectedNodeId: id })),

  updateNodeData: (id, data) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id
          ? {
              ...node,
              data: {
                ...node.data,
                ...data,
              },
            }
          : node,
      ),
    })),

  appendLog: (line) =>
    set((state) => ({ executionLogs: [...state.executionLogs, line] })),

  clearLogs: () =>
    set(() => ({ executionLogs: ['[console] Logs limpos pelo usuário.'] })),

  setSessionId: (id) => set(() => ({ sessionId: id })),

  setRunState: (state) => set(() => ({ runState: state })),

  setNodeStatus: (nodeId, status) =>
    set((state) => ({
      nodeStatuses: {
        ...state.nodeStatuses,
        [nodeId]: status,
      },
    })),

  setLastResult: (result) => set(() => ({ lastResult: result })),

  setBackendOnline: (value) => set(() => ({ backendOnline: value })),

  resetRun: () =>
    set(() => ({
      sessionId: null,
      runState: 'idle',
      nodeStatuses: {},
      lastResult: null,
    })),

  saveFlow: async (name, description = '') => {
    const { nodes, edges } = get();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const config = {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      })),
    };

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows`, {
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

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/${flowId}`, {
      headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
    });

    const flow = await response.json();

    set({
      nodes: flow.config?.nodes ?? [],
      edges: flow.config?.edges ?? [],
    });
  },
}));

// Utilitário para mapear automaticamente templates por nome.
export function findTemplateByAgentName(agentName: string): AgentTemplate | undefined {
  const normalized = agentName.toLowerCase();
  return AGENT_TEMPLATES.find((template) =>
    normalized.includes(template.name.toLowerCase().replace('agent', '')),
  );
}
