'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/lib/supabase/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Stats {
  totalUsers: number;
  totalFlows: number;
  totalExecutions: number;
  executionsToday: number;
  avgDuration: number;
  totalCost: number;
}

export default function AdminDashboard() {
  const { profile, loading } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentExecutions, setRecentExecutions] = useState<any[]>([]);
  const [recentUsers, setRecentUsers] = useState<any[]>([]);
  const [executionsByDay, setExecutionsByDay] = useState<any[]>([]);

  useEffect(() => {
    if (profile?.role === 'admin') {
      loadStats();
      loadRecentExecutions();
      loadRecentUsers();
      loadExecutionsByDay();
    }
  }, [profile]);

  async function loadStats() {
    const [users, flows, executions] = await Promise.all([
      supabase.from('profiles').select('id', { count: 'exact', head: true }),
      supabase.from('flows').select('id', { count: 'exact', head: true }),
      supabase.from('executions').select('*', { count: 'exact' }),
    ]);

    const today = new Date().toISOString().split('T')[0];
    const execRows = executions.data ?? [];
    const executionsToday = execRows.filter((e) => e.started_at?.startsWith(today)).length;
    const durations = execRows.filter((e) => e.duration_seconds).map((e) => e.duration_seconds);
    const avgDuration = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0;
    const totalCost = execRows.reduce((sum, e) => sum + (parseFloat(e.cost_usd) || 0), 0);

    setStats({
      totalUsers: users.count || 0,
      totalFlows: flows.count || 0,
      totalExecutions: executions.count || 0,
      executionsToday,
      avgDuration,
      totalCost,
    });
  }

  async function loadRecentExecutions() {
    const { data } = await supabase.from('executions').select('*, profiles(email)').order('started_at', { ascending: false }).limit(10);
    setRecentExecutions(data || []);
  }

  async function loadRecentUsers() {
    const { data } = await supabase.from('profiles').select('*').order('created_at', { ascending: false }).limit(10);
    setRecentUsers(data || []);
  }

  async function loadExecutionsByDay() {
    const { data } = await supabase.from('executions').select('started_at, status').gte('started_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());
    const grouped = (data || []).reduce((acc: Record<string, any>, exec: any) => {
      const day = exec.started_at.split('T')[0];
      if (!acc[day]) acc[day] = { date: day, executions: 0 };
      acc[day].executions++;
      return acc;
    }, {});
    setExecutionsByDay(Object.values(grouped));
  }

  if (loading) return <div>Carregando...</div>;
  if (profile?.role !== 'admin') return <div>Acesso negado</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard title="Usuários" value={stats?.totalUsers || 0} />
        <StatCard title="Fluxos" value={stats?.totalFlows || 0} />
        <StatCard title="Execuções" value={stats?.totalExecutions || 0} />
        <StatCard title="Hoje" value={stats?.executionsToday || 0} />
      </div>
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={executionsByDay}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Bar dataKey="executions" fill="#3b82f6" /></BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white rounded-lg shadow p-4">
        {recentUsers.slice(0, 5).map((u) => (
          <div key={u.id} className="flex justify-between border-b py-2">
            <span>{u.email}</span>
            <span className="text-gray-500 text-sm">{formatDistanceToNow(new Date(u.created_at), { locale: ptBR })}</span>
          </div>
        ))}
      </div>
      <div className="hidden">{recentExecutions.length}</div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string | number }) {
  return <div className="bg-white rounded-lg shadow p-4"><p className="text-sm text-gray-500">{title}</p><p className="text-2xl font-bold">{value}</p></div>;
}
