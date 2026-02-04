'use client';

import React, { useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Task } from '@ads/shared';

interface VisualCanvasProps {
  tasks: Task[];
}

export default function VisualCanvas({ tasks }: VisualCanvasProps) {
  const nodes: Node[] = useMemo(() => {
    return tasks.map((task, index) => ({
      id: task.id,
      data: { label: task.title },
      position: { x: 250, y: index * 100 + 50 },
      style: {
        background: task.status === 'completed' ? '#dcfce7' : '#f3f4f6',
        border: '1px solid #3b82f6',
        borderRadius: '8px',
        padding: '10px',
        fontSize: '12px',
        fontWeight: 'bold',
        width: 200,
        textAlign: 'center' as const
      }
    }));
  }, [tasks]);

  const edges: Edge[] = useMemo(() => {
    const result: Edge[] = [];
    for (let i = 0; i < tasks.length - 1; i++) {
      result.push({
        id: `e-${tasks[i].id}-${tasks[i+1].id}`,
        source: tasks[i].id,
        target: tasks[i+1].id,
        animated: tasks[i].status === 'running',
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
      });
    }
    return result;
  }, [tasks]);

  return (
    <div className="h-full w-full bg-white border rounded-lg overflow-hidden min-h-[500px]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
