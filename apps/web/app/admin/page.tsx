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
  const [lang, setLang] = useState<'en' | 'pt'>('pt');
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentExecutions, setRecentExecutions] = useState<any[]>([]);
  const [recentUsers, setRecentUsers] = useState<any[]>([]);
  const [executionsByDay, setExecutionsByDay] = useState<any[]>([]);
  const [testResult, setTestResult] = useState<string>('');

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

  const runTest = async (endpoint: string) => {
    setTestResult('TESTING...');
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
      const r = await fetch(`${apiBase}${endpoint}`);
      const data = await r.json();
      setTestResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setTestResult(`ERROR: ${err.message}`);
    }
  };

  if (loading) return <div className="p-8 bg-black text-cyber-cyan font-mono">INITIALIZING_ADMIN_INTERFACE...</div>;
  if (profile?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-8">
        <div className="border border-red-500 bg-red-500/10 p-8 text-center">
          <h1 className="text-red-500 font-black tracking-widest uppercase mb-4 text-2xl">ACCESS_DENIED</h1>
          <p className="text-red-400 font-mono text-xs">CRITICAL: UNAUTHORIZED_ACCESS_DETECTED. ADMINISTRATOR_LEVEL_REQUIRED.</p>
        </div>
      </div>
    );
  }

  const content = {
    en: {
      title: 'SYSTEM_ADMIN_HUB',
      functionalities: 'AGENT_CAPABILITIES',
      status: 'DEPLOYMENT_STATUS',
      credentials: 'ENCRYPTION_KEYS_REQUIRED',
      playground: 'API_STRESS_TEST_PLAYGROUND',
      agents: [
        { name: 'TravelAgent', desc: 'Researches flights, hotels, and generates travel itineraries with costs.' },
        { name: 'FinancialAgent', desc: 'Analyzes stock market data (YFinance) and calculates ROI/Costs.' },
        { name: 'MeetingAgent', desc: 'Schedules Google Calendar events and manages attendees.' },
        { name: 'MarketingAgent', desc: 'Generates market reports and social media campaign strategies.' },
        { name: 'ExcelAgent', desc: 'Processes spreadsheets, generates reports and complex tables.' },
        { name: 'PhoneAgent', desc: 'Performs automated VoIP calls via Twilio with AI scripts.' },
      ]
    },
    pt: {
      title: 'CENTRAL_DE_CONTROLE_ADMIN',
      functionalities: 'CAPACIDADES_DOS_AGENTES',
      status: 'STATUS_DE_DESENVOLVIMENTO',
      credentials: 'CHAVES_DE_ACESSO_NECESSÁRIAS',
      playground: 'PLAYGROUND_DE_TESTES_DE_API',
      agents: [
        { name: 'AgenteTurismo', desc: 'Pesquisa voos, hotéis e gera itinerários com custos detalhados.' },
        { name: 'AgenteFinanceiro', desc: 'Analisa dados do mercado (YFinance) e calcula ROI/Custos.' },
        { name: 'AgenteReuniao', desc: 'Agenda eventos no Google Calendar e gerencia participantes.' },
        { name: 'AgenteMarketing', desc: 'Gera relatórios de mercado e estratégias de campanha.' },
        { name: 'AgenteExcel', desc: 'Processa planilhas, gera relatórios e tabelas complexas.' },
        { name: 'AgenteTelefone', desc: 'Realiza chamadas VoIP automatizadas via Twilio com scripts de IA.' },
      ]
    }
  };

  const t = content[lang];

  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-cyber-cyan selection:text-black">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-12 border-b border-white/10 pb-6">
          <h1 className="text-4xl font-black tracking-tighter italic uppercase">
            <span className="text-cyber-cyan">_</span>{t.title}
          </h1>
          <div className="flex bg-white/5 border border-white/10 p-0.5">
            <button onClick={() => setLang('en')} className={`px-3 py-1 text-[10px] font-bold ${lang === 'en' ? 'bg-cyber-cyan text-black' : 'text-white/40'}`}>EN</button>
            <button onClick={() => setLang('pt')} className={`px-3 py-1 text-[10px] font-bold ${lang === 'pt' ? 'bg-cyber-cyan text-black' : 'text-white/40'}`}>PT</button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <StatCard title={lang === 'en' ? 'USERS' : 'USUÁRIOS'} value={stats?.totalUsers || 0} icon="👥" />
          <StatCard title={lang === 'en' ? 'FLOWS' : 'FLUXOS'} value={stats?.totalFlows || 0} icon="🔄" />
          <StatCard title={lang === 'en' ? 'EXECUTIONS' : 'EXECUÇÕES'} value={stats?.totalExecutions || 0} icon="▶️" />
          <StatCard title={lang === 'en' ? 'TODAY' : 'HOJE'} value={stats?.executionsToday || 0} icon="📊" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
          {/* Functionalities */}
          <div className="glass-panel p-6 border-cyber-cyan/20">
            <h2 className="text-sm font-black tracking-widest text-cyber-cyan uppercase mb-6 flex items-center gap-2">
              <div className="h-4 w-1 bg-cyber-cyan" /> {t.functionalities}
            </h2>
            <div className="space-y-4">
              {t.agents.map((a) => (
                <div key={a.name} className="border-l border-white/10 pl-4 py-1">
                  <p className="text-[11px] font-black text-white mb-1 uppercase tracking-tighter">{a.name}</p>
                  <p className="text-[10px] text-neutral-500 leading-relaxed uppercase">{a.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Development Status */}
          <div className="glass-panel p-6 border-cyber-magenta/20">
            <h2 className="text-sm font-black tracking-widest text-cyber-magenta uppercase mb-6 flex items-center gap-2">
              <div className="h-4 w-1 bg-cyber-magenta" /> {t.status}
            </h2>
            <div className="space-y-6">
              <div>
                <p className="text-[10px] font-black text-emerald-400 mb-2">[ READY_FOR_DEPLOYMENT ]</p>
                <p className="text-[9px] text-neutral-400 uppercase leading-relaxed">
                  - Multi-Agent Orchestration Engine (LangGraph)<br />
                  - Real-time Execution Streaming (WebSockets)<br />
                  - Visual Flow Designer (ReactFlow)<br />
                  - Core Financial and Excel Agents
                </p>
              </div>
              <div>
                <p className="text-[10px] font-black text-cyber-yellow mb-2">[ IN_DEVELOPMENT ]</p>
                <p className="text-[9px] text-neutral-400 uppercase leading-relaxed">
                  - Advanced VoIP Real-time Interaction<br />
                  - Multi-user Collaboration in Canvas<br />
                  - Agent Memory Persistence (Vector DB)<br />
                  - Custom Tool Upload (.py / .js)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Credentials */}
        <div className="glass-panel p-6 border-white/10 mb-12">
          <h2 className="text-sm font-black tracking-widest text-white uppercase mb-6 flex items-center gap-2">
            <div className="h-4 w-1 bg-white" /> {t.credentials}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="bg-white/5 p-4 border border-white/5">
                <p className="text-[10px] font-black mb-1">BRAIN_MODELS</p>
                <p className="text-[9px] text-neutral-500">OPENAI_API_KEY, ANTHROPIC_API_KEY</p>
             </div>
             <div className="bg-white/5 p-4 border border-white/5">
                <p className="text-[10px] font-black mb-1">COMMS_VIRTUAL</p>
                <p className="text-[9px] text-neutral-500">TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN</p>
             </div>
             <div className="bg-white/5 p-4 border border-white/5">
                <p className="text-[10px] font-black mb-1">DATA_STORAGE</p>
                <p className="text-[9px] text-neutral-500">SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY</p>
             </div>
          </div>
        </div>

        {/* Playground */}
        <div className="glass-panel p-6 border-cyber-cyan/20 mb-12">
          <h2 className="text-sm font-black tracking-widest text-cyber-cyan uppercase mb-6 flex items-center gap-2">
            <div className="h-4 w-1 bg-cyber-cyan" /> {t.playground}
          </h2>
          <div className="flex gap-3 mb-6">
             <button onClick={() => runTest('/health')} className="btn-cyber-outline !px-4 !py-2 !text-[10px]">GET /health</button>
             <button onClick={() => runTest('/api/agents/templates')} className="btn-cyber-outline !px-4 !py-2 !text-[10px]">GET /templates</button>
             <button onClick={() => runTest('/api/metrics')} className="btn-cyber-outline !px-4 !py-2 !text-[10px]">GET /metrics</button>
          </div>
          <pre className="bg-black/50 border border-white/10 p-4 text-[10px] text-emerald-500 overflow-auto max-h-60 custom-scrollbar font-mono">
            {testResult || 'AWAITING_COMMAND...'}
          </pre>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <StatCard title="Duração Média" value={`${stats?.avgDuration || 0}s`} icon="⏱️" />
          <StatCard title="Custo Total" value={`$${(stats?.totalCost ?? 0).toFixed(2)}`} icon="💰" />
        </div>

        <div className="glass-panel p-6 border-white/10 mb-12">
          <h2 className="text-sm font-black tracking-widest text-white uppercase mb-6 flex items-center gap-2">
             <div className="h-4 w-1 bg-white" /> {lang === 'en' ? 'EXECUTIONS_HISTORY_7D' : 'HISTÓRICO_EXECUÇÕES_7D'}
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={executionsByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" fontSize={10} />
              <YAxis stroke="rgba(255,255,255,0.5)" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '1px solid rgba(0,243,255,0.2)', fontSize: '10px' }}
                itemStyle={{ color: '#00f3ff' }}
              />
              <Bar dataKey="executions" fill="#00f3ff" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-panel p-6 border-white/10 mb-12">
          <h2 className="text-sm font-black tracking-widest text-white uppercase mb-6 flex items-center gap-2">
             <div className="h-4 w-1 bg-white" /> {lang === 'en' ? 'RECENT_EXECUTIONS' : 'EXECUÇÕES_RECENTES'}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[10px]">
              <thead>
                <tr className="border-b border-white/10 text-neutral-500">
                  <th className="text-left py-4 uppercase tracking-widest">IDENTITY</th>
                  <th className="text-left py-4 uppercase tracking-widest">STATUS_CODE</th>
                  <th className="text-left py-4 uppercase tracking-widest">TIME_ELAPSED</th>
                  <th className="text-left py-4 uppercase tracking-widest">TIMESTAMP</th>
                </tr>
              </thead>
              <tbody>
                {recentExecutions.map((exec) => (
                  <tr key={exec.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-4 text-white font-bold">{exec.profiles?.email}</td>
                    <td className="py-4">
                      <StatusBadge status={exec.status} />
                    </td>
                    <td className="py-4 text-neutral-400">{exec.duration_seconds || 0}s</td>
                    <td className="py-4 text-neutral-600 italic">
                      {formatDistanceToNow(new Date(exec.started_at), { locale: lang === 'pt' ? ptBR : undefined, addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-panel p-6 border-white/10">
          <h2 className="text-sm font-black tracking-widest text-white uppercase mb-6 flex items-center gap-2">
             <div className="h-4 w-1 bg-white" /> {lang === 'en' ? 'RECENT_USERS' : 'USUÁRIOS_RECENTES'}
          </h2>
          <div className="space-y-4">
            {recentUsers.map((user) => (
              <div key={user.id} className="flex items-center justify-between border-b border-white/5 pb-4 last:border-0 last:pb-0">
                <div>
                  <p className="text-[11px] font-black text-white uppercase">{user.full_name || 'UNKNOWN_IDENTITY'}</p>
                  <p className="text-[10px] text-neutral-500 font-mono">{user.email}</p>
                </div>
                <div className="text-right">
                  <p className="text-[9px] text-neutral-600 font-mono mb-2 uppercase">
                    {formatDistanceToNow(new Date(user.created_at), { locale: lang === 'pt' ? ptBR : undefined, addSuffix: true })}
                  </p>
                  <span
                    className={`text-[8px] font-black px-2 py-0.5 uppercase tracking-tighter ${
                      user.role === 'admin'
                        ? 'bg-cyber-magenta/20 text-cyber-magenta border border-cyber-magenta/30'
                        : 'bg-white/5 text-neutral-400 border border-white/10'
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
    <div className="glass-panel p-6 border-white/5 hover:border-cyber-cyan/30 transition-colors group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest mb-2">{title}</p>
          <p className="text-3xl font-black text-white italic group-hover:text-cyber-cyan transition-colors">{value}</p>
        </div>
        <div className="text-3xl opacity-20 group-hover:opacity-100 transition-opacity">{icon}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: 'bg-cyber-yellow/20 text-cyber-yellow border-cyber-yellow/30',
    done: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    error: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <span className={`text-[9px] font-black px-2 py-0.5 border uppercase tracking-tighter ${colors[status] || 'bg-white/5 text-neutral-400 border-white/10'}`}>
      {status}
    </span>
  );
}
