'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { Run, Task, TaskLog, Artifact } from '@ads/shared';

export default function RunDetailPage() {
  const { id } = useParams();
  const [run, setRun] = useState<Run | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [logs, setLogs] = useState<TaskLog[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [executing, setExecuting] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchRun();
    fetchTasks();
  }, [id]);

  useEffect(() => {
    if (selectedTaskId) {
      fetchArtifacts(selectedTaskId);
      const interval = setInterval(() => {
        fetchLogs(selectedTaskId);
        fetchTasks();
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [selectedTaskId]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  async function fetchRun() {
    const { data } = await supabase.from('runs').select('*').eq('id', id).single();
    if (data) setRun(data);
  }

  async function fetchTasks() {
    const { data } = await supabase.from('tasks').select('*').eq('run_id', id).order('order_index', { ascending: true });
    if (data) {
      setTasks(data);
      if (!selectedTaskId && data.length > 0) setSelectedTaskId(data[0].id);
    }
  }

  async function fetchLogs(taskId: string) {
    const response = await fetch(`/api/tasks/${taskId}/stream`);
    const data = await response.json();
    if (Array.isArray(data)) setLogs(data);
  }

  async function fetchArtifacts(taskId: string) {
    const { data } = await supabase.from('artifacts').select('*').eq('task_id', taskId);
    if (data) setArtifacts(data);
  }

  const handleExecuteTask = async (taskId: string) => {
    setExecuting(true);
    try {
      await fetch(`/api/tasks/${taskId}/execute`, { method: 'POST' });
    } catch (err) {
      console.error(err);
    } finally {
      setExecuting(false);
    }
  };

  const selectedTask = tasks.find(t => t.id === selectedTaskId);

  if (!run) return <div className="p-8">Loading run...</div>;

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="w-80 bg-white border-r flex flex-col">
        <div className="p-4 border-b bg-gray-50">
          <Link href={`/projects/${run.project_id}`} className="text-sm text-blue-600 hover:underline mb-2 block">← Back to Project</Link>
          <h1 className="font-bold text-lg line-clamp-2">{run.objective}</h1>
        </div>
        <div className="flex-1 overflow-auto p-4 space-y-2">
          <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Tasks</h2>
          {tasks.map((task) => (
            <button
              key={task.id}
              onClick={() => { setSelectedTaskId(task.id); setLogs([]); }}
              className={`w-full text-left p-3 rounded-lg border transition ${
                selectedTaskId === task.id ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'hover:bg-gray-50 border-gray-200'
              }`}
            >
              <div className="font-semibold text-sm">{task.title}</div>
              <div className="flex items-center justify-between mt-1">
                <span className={`text-[10px] uppercase px-1 rounded font-bold ${
                  task.status === 'completed' ? 'bg-green-100 text-green-700' :
                  task.status === 'failed' ? 'bg-red-100 text-red-700' :
                  task.status === 'running' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {task.status}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedTask ? (
          <>
            <div className="p-6 bg-white border-b flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">{selectedTask.title}</h2>
                <p className="text-gray-500">{selectedTask.description}</p>
              </div>
              <button
                onClick={() => handleExecuteTask(selectedTask.id)}
                disabled={executing || selectedTask.status === 'running'}
                className="bg-green-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-green-700 disabled:opacity-50"
              >
                {selectedTask.status === 'todo' ? 'Execute Task' : 'Re-run Task'}
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6 space-y-6">
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 min-h-[300px] shadow-inner">
                <div className="flex justify-between items-center mb-2 border-b border-gray-800 pb-2 text-gray-500 uppercase text-xs">
                  <span>Execution Logs</span>
                  {selectedTask.status === 'running' && <span className="animate-pulse">Running...</span>}
                </div>
                {logs.map((log) => (
                  <div key={log.id} className="mb-1 leading-relaxed">
                    <span className="text-gray-600 mr-2">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                    {log.line}
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>

              {selectedTask.patch && (
                <div className="bg-white border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b font-bold text-sm">Proposed Changes (Diff)</div>
                  <pre className="p-4 overflow-auto max-h-96 text-xs bg-gray-50 text-gray-800 whitespace-pre-wrap">
                    {selectedTask.patch}
                  </pre>
                </div>
              )}

              {artifacts.length > 0 && (
                <div className="bg-white border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b font-bold text-sm">Artifacts</div>
                  <div className="divide-y">
                    {artifacts.map((art) => (
                      <div key={art.id} className="p-4 flex justify-between items-center">
                        <span className="font-medium">{art.name}</span>
                        <a
                          href={`${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/artifacts/${art.storage_path}`}
                          target="_blank" rel="noreferrer"
                          className="text-blue-600 hover:underline text-sm font-bold"
                        >
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">Select a task</div>
        )}
      </div>
    </div>
  );
}
