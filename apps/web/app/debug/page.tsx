'use client';

import { useState } from 'react';
import { healthCheck, runFlow } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

export default function DebugPage() {
  const { profile } = useAuth();
  const [backendStatus, setBackendStatus] = useState<boolean | null>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function testBackend() {
    setLoading(true);
    const isOnline = await healthCheck();
    setBackendStatus(isOnline);
    setLoading(false);
  }

  async function testSimpleAgent() {
    setLoading(true);
    try {
      const result = await runFlow({
        session_id: crypto.randomUUID(),
        nodes: [{ id: 'test-1', agent_type: 'financial', label: 'Teste Financeiro', model: 'claude-3-5-sonnet-20241022', provider: 'anthropic', system_prompt: '', tools: ['finance'] }],
        edges: [],
        inputs: { objetivo: 'Teste rápido: análise de AAPL' },
      });
      setTestResult(result);
    } catch (err: any) {
      setTestResult({ error: err.message });
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-8">🛠️ Debug & Test Playground</h1>
      <button onClick={testBackend} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded mr-2">Testar Conexão</button>
      <button onClick={testSimpleAgent} disabled={loading} className="px-4 py-2 bg-green-600 text-white rounded">Executar Agente de Teste</button>
      {backendStatus !== null && <p className="mt-4">{backendStatus ? '✅ Backend Online' : '❌ Backend Offline'}</p>}
      {testResult && <pre className="mt-4 p-4 bg-white rounded">{JSON.stringify(testResult, null, 2)}</pre>}
      <pre className="mt-4 p-4 bg-white rounded">{JSON.stringify(profile, null, 2)}</pre>
    </div>
  );
}
