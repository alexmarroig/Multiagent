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
        nodes: [
          {
            id: 'test-1',
            agent_type: 'financial',
            label: 'Teste Financeiro',
            model: 'claude-3-5-sonnet-20241022',
            provider: 'anthropic',
            system_prompt: '',
            tools: ['finance'],
          },
        ],
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 dark:text-white">🛠️ Debug & Test Playground</h1>

        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Backend Status</h2>
            <button
              onClick={testBackend}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Testar Conexão
            </button>
            {backendStatus !== null && (
              <div
                className={`mt-4 p-4 rounded ${
                  backendStatus
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}
              >
                {backendStatus ? '✅ Backend Online' : '❌ Backend Offline'}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Test Agent Execution</h2>
            <button
              onClick={testSimpleAgent}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              Executar Agente de Teste
            </button>
            {testResult && (
              <pre className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded text-sm overflow-auto dark:text-gray-300">
                {JSON.stringify(testResult, null, 2)}
              </pre>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Current User</h2>
            <pre className="p-4 bg-gray-100 dark:bg-gray-700 rounded text-sm overflow-auto dark:text-gray-300">
              {JSON.stringify(profile, null, 2)}
            </pre>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Environment Variables</h2>
            <pre className="p-4 bg-gray-100 dark:bg-gray-700 rounded text-sm dark:text-gray-300">
              {`API_URL: ${process.env.NEXT_PUBLIC_API_URL}
WS_URL: ${process.env.NEXT_PUBLIC_WS_URL}
SUPABASE_URL: ${process.env.NEXT_PUBLIC_SUPABASE_URL?.substring(0, 30)}...`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
