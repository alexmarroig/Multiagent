'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { Project } from '@ads/shared';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  async function fetchProjects() {
    const { data, error } = await supabase.from('projects').select('*').order('created_at', { ascending: false });
    if (data) setProjects(data);
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase.from('projects').insert({
      user_id: user.id,
      name,
      repo_url: repoUrl,
      default_branch: 'main'
    });

    if (error) alert(error.message);
    else {
      setName('');
      setRepoUrl('');
      fetchProjects();
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Projects</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Your Projects</h2>
          {projects.length === 0 && <p className="text-gray-500 italic">No projects found.</p>}
          <div className="grid gap-4">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/projects/${project.id}`}
                className="block p-4 bg-white rounded-lg border shadow-sm hover:shadow-md transition"
              >
                <div className="font-bold text-lg text-blue-600">{project.name}</div>
                <div className="text-sm text-gray-500">{project.repo_url}</div>
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm h-fit">
          <h2 className="text-xl font-semibold mb-4">Create New Project</h2>
          <form onSubmit={handleCreateProject} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Project Name</label>
              <input
                className="w-full p-2 border rounded"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Awesome App"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">GitHub Repo URL</label>
              <input
                className="w-full p-2 border rounded"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded font-bold hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Project'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
