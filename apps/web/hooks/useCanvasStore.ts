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
} from '@/types/agentos';

type CanvasStore = {
  nodes: Node<AgentNodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  executionLogs: string[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNodeFromTemplate: (template: AgentTemplate) => void;
  selectNode: (id: string | null) => void;
  updateNodeData: (id: string, data: Partial<AgentNodeData>) => void;
  appendLog: (line: string) => void;
  clearLogs: () => void;
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
      model: 'gpt-4.1',
      prompt: AGENT_TEMPLATES.find((t) => t.id === 'supervisor-agent')?.defaultPrompt ?? '',
      tools: ['langgraph', 'evaluation'],
    },
  },
];

export const useCanvasStore = create<CanvasStore>((set) => ({
  nodes: defaultNodes,
  edges: [],
  selectedNodeId: defaultNodes[0].id,
  executionLogs: [
    '[boot] AgentOS canvas inicializado.',
    '[hint] Arraste agentes da sidebar para o canvas.',
  ],

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
}));
