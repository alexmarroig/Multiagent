'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signUp } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 6) {
      setError('Senha deve ter no mínimo 6 caracteres');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await signUp(email, password, fullName);
      router.push('/agentos');
    } catch (err: any) {
      setError(err.message || 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full space-y-8 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-lg">
        <h2 className="text-center text-3xl font-bold text-gray-900 dark:text-white">AgentOS</h2>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">{error}</div>}
          <div className="space-y-4">
            <input type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} className="block w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Seu Nome" />
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="block w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="seu@email.com" />
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="block w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="••••••••" />
          </div>
          <button type="submit" disabled={loading} className="w-full py-2 px-4 rounded-md text-white bg-blue-600 hover:bg-blue-700">
            {loading ? 'Criando conta...' : 'Criar conta'}
          </button>
          <div className="text-center text-sm">
            <span className="text-gray-600 dark:text-gray-400">Já tem conta? </span>
            <Link href="/login" className="text-blue-600">Entrar</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
