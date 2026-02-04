'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { Project, Run } from '@ads/shared';

export default function ProjectDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [objective, setObjective] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProject();
    fetchRuns();
  }, [id]);

  async function fetchProject() {
    const { data } = await supabase.from('projects').select('*').eq('id', id).single();
    if (data) setProject(data);
  }

  async function fetchRuns() {
    const { data } = await supabase.from('runs').select('*').eq('project_id', id).order('created_at', { ascending: false });
    if (data) setRuns(data);
  }

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: id,
          objective: objective,
        }),
      });

      if (!response.ok) throw new Error('Failed to create run');

      const { run_id } = await response.json();
      router.push(`/runs/${run_id}`);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!project) return <div className="p-8 text-gray-500">Loading project...</div>;

  return (
    <div className="p-8">
      <Link href="/projects" className="text-blue-600 hover:underline mb-4 block">← Back to Projects</Link>
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
          <p className="text-gray-500">{project.repo_url} (branch: {project.default_branch})</p>
        </div>
        <Link
          href={`/projects/${id}/workflow`}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-purple-700 transition flex items-center gap-2"
        >
          <span>Visual Workflow Builder</span>
          <span className="bg-purple-500 px-2 py-0.5 rounded text-[10px] uppercase">n8n Style</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">Previous Runs</h2>
          {runs.length === 0 && <p className="text-gray-500 italic">No runs yet.</p>}
          <div className="grid gap-4">
            {runs.map((run) => (
              <Link
                key={run.id}
                href={`/runs/${run.id}`}
                className="block p-4 bg-white rounded-lg border shadow-sm hover:shadow-md transition"
              >
                <div className="flex justify-between items-start">
                  <div className="font-semibold text-lg line-clamp-1">{run.objective}</div>
                  <span className={`text-xs px-2 py-1 rounded uppercase font-bold ${
                    run.status === 'completed' ? 'bg-green-100 text-green-700' :
                    run.status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {run.status}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  {new Date(run.created_at).toLocaleString()}
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm h-fit">
          <h2 className="text-xl font-semibold mb-4">Start New Run</h2>
          <form onSubmit={handleCreateRun} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">What is the objective?</label>
              <textarea
                className="w-full p-2 border rounded h-32"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder="Ex: Create a new page for user profile, or generate a report of all users in xlsx"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded font-bold hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Initializing Agent...' : 'Start Agentic Run'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
