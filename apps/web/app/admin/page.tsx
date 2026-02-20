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
    const execRows = executions.data || [];
    const executionsToday = execRows.filter((e) => e.started_at?.startsWith(today)).length || 0;

    const durations = execRows.filter((e) => e.duration_seconds).map((e) => e.duration_seconds) || [];
    const avgDuration = durations.length
      ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
      : 0;

    const totalCost = execRows.reduce((sum, e) => sum + (parseFloat(e.cost_usd) || 0), 0) || 0;

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
    const { data } = await supabase
      .from('executions')
      .select(`
        *,
        profiles!inner(email)
      `)
      .order('started_at', { ascending: false })
      .limit(10);
    setRecentExecutions(data || []);
  }

  async function loadRecentUsers() {
    const { data } = await supabase.from('profiles').select('*').order('created_at', { ascending: false }).limit(10);
    setRecentUsers(data || []);
  }

  async function loadExecutionsByDay() {
    const { data } = await supabase
      .from('executions')
      .select('started_at, status')
      .gte('started_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

    const grouped = (data || []).reduce((acc: any, exec: any) => {
      const day = exec.started_at.split('T')[0];
      if (!acc[day]) acc[day] = { date: day, executions: 0 };
      acc[day].executions++;
      return acc;
    }, {});

    setExecutionsByDay(Object.values(grouped));
  }

  if (loading) return <div className="p-8">Carregando...</div>;
  if (profile?.role !== 'admin') {
    return <div className="p-8 text-center text-red-600">Acesso negado. Apenas admins.</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">🛠️ Admin Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard title="Usuários" value={stats?.totalUsers || 0} icon="👥" />
          <StatCard title="Fluxos" value={stats?.totalFlows || 0} icon="🔄" />
          <StatCard title="Execuções" value={stats?.totalExecutions || 0} icon="▶️" />
          <StatCard title="Hoje" value={stats?.executionsToday || 0} icon="📊" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <StatCard title="Duração Média" value={`${stats?.avgDuration || 0}s`} icon="⏱️" />
          <StatCard title="Custo Total" value={`$${(stats?.totalCost ?? 0).toFixed(2)}`} icon="💰" />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 dark:text-white">Execuções (últimos 7 dias)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={executionsByDay}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="executions" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 dark:text-white">Execuções Recentes</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b dark:border-gray-700">
                  <th className="text-left py-2 text-sm font-medium dark:text-gray-300">Usuário</th>
                  <th className="text-left py-2 text-sm font-medium dark:text-gray-300">Status</th>
                  <th className="text-left py-2 text-sm font-medium dark:text-gray-300">Duração</th>
                  <th className="text-left py-2 text-sm font-medium dark:text-gray-300">Há</th>
                </tr>
              </thead>
              <tbody>
                {recentExecutions.map((exec) => (
                  <tr key={exec.id} className="border-b dark:border-gray-700">
                    <td className="py-2 text-sm dark:text-gray-300">{exec.profiles?.email}</td>
                    <td className="py-2">
                      <StatusBadge status={exec.status} />
                    </td>
                    <td className="py-2 text-sm dark:text-gray-300">{exec.duration_seconds || 0}s</td>
                    <td className="py-2 text-sm text-gray-500 dark:text-gray-400">
                      {formatDistanceToNow(new Date(exec.started_at), { locale: ptBR })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 dark:text-white">Usuários Recentes</h2>
          <div className="space-y-3">
            {recentUsers.map((user) => (
              <div key={user.id} className="flex items-center justify-between border-b dark:border-gray-700 pb-3">
                <div>
                  <p className="font-medium dark:text-white">{user.full_name || 'Sem nome'}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDistanceToNow(new Date(user.created_at), { locale: ptBR })}
                  </p>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      user.role === 'admin'
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string | number; icon: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold dark:text-white mt-1">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    done: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  return (
    <span className={`text-xs px-2 py-1 rounded ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
}
