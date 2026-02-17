'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.push('/agentos');
  }, [user, loading, router]);

  if (loading) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6">AgentOS</h1>
        <p className="text-2xl text-gray-600 mb-12">Crie agentes de IA autônomos sem código</p>
        <div className="flex gap-4 justify-center">
          <Link href="/signup" className="px-8 py-4 bg-blue-600 text-white rounded-lg">Começar Grátis</Link>
          <Link href="/login" className="px-8 py-4 bg-white text-blue-600 rounded-lg border border-blue-600">Entrar</Link>
        </div>
      </div>
    </div>
  );
}
