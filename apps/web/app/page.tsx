'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/agentos');
    }
  }, [user, loading, router]);

  if (loading) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-6">AgentOS</h1>
          <p className="text-2xl text-gray-600 dark:text-gray-300 mb-12">Crie agentes de IA autônomos sem código</p>

          <div className="flex gap-4 justify-center mb-24">
            <Link
              href="/signup"
              className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 shadow-lg transition"
            >
              Começar Grátis
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 text-lg font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 shadow-lg border border-blue-600 transition"
            >
              Entrar
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon="🎨"
              title="Visual & Drag-and-Drop"
              description="Monte fluxos de agentes arrastando nós no canvas visual"
            />
            <FeatureCard
              icon="🤖"
              title="7 Tipos de Agente"
              description="Financeiro, Viagem, Excel, Marketing, Telefone e mais"
            />
            <FeatureCard
              icon="⚡"
              title="Execução em Tempo Real"
              description="Veja cada passo dos agentes acontecendo ao vivo"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 hover:shadow-xl transition">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 dark:text-white">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}
