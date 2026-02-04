'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import WorkflowEditor from '@/components/WorkflowEditor';

export default function WorkflowPage() {
  const { id } = useParams();

  return (
    <div className="p-8 h-screen flex flex-col">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <Link href={`/projects/${id}`} className="text-blue-600 hover:underline mb-2 block">← Back to Project</Link>
          <h1 className="text-3xl font-bold">Visual Workflow Builder</h1>
          <p className="text-gray-500 italic text-sm">Design your agentic flow (n8n style)</p>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <WorkflowEditor projectId={id as string} />
      </div>
    </div>
  );
}
