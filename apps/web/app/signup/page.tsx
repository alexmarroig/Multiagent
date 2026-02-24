'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

const ease = [0.16, 1, 0.3, 1] as const;

export default function SignupPage() {
  const { signUp } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 6) {
      setError('A senha deve conter ao menos 6 caracteres.');
      return;
    }

    setLoading(true);
    setError('');
    setToast('');

    try {
      await signUp(email, password, fullName);
      setToast('Conta criada. Verifique seu e-mail para confirmação.');
    } catch (err: any) {
      setError(err?.message || 'Não foi possível concluir o cadastro.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#05070d] px-4">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_15%,rgba(59,130,246,0.2),transparent_40%),radial-gradient(circle_at_80%_75%,rgba(29,78,216,0.15),transparent_35%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.04] [background-image:radial-gradient(#fff_0.5px,transparent_0.5px)] [background-size:3px_3px]" />
      <div className="pointer-events-none absolute h-[300px] w-[300px] rounded-full bg-blue-500/20 blur-[95px]" />

      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease }}
        className="relative w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl"
      >
        <h1 className="text-2xl font-semibold text-white">Infraestrutura de Inteligência Financeira</h1>
        <p className="mt-2 text-sm text-gray-400">Acesse sua plataforma institucional.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Nome completo"
            className="w-full rounded-lg border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-gray-500 outline-none transition-all duration-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/35"
          />
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email@empresa.com"
            className="w-full rounded-lg border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-gray-500 outline-none transition-all duration-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/35"
          />
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full rounded-lg border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-gray-500 outline-none transition-all duration-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/35"
          />

          {error && <p className="text-xs text-red-300">{error}</p>}

          <motion.button
            whileHover={{ scale: 1.04 }}
            transition={{ duration: 0.4, ease }}
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-700 px-4 py-3 text-sm font-semibold text-white shadow-[0_0_32px_rgba(59,130,246,0.35)] disabled:opacity-60"
          >
            {loading ? 'Provisionando conta...' : 'Criar conta'}
          </motion.button>
        </form>

        <p className="mt-5 text-center text-sm text-gray-400">
          Já possui acesso?{' '}
          <Link className="text-blue-300 hover:text-blue-200" href="/login">
            Entrar
          </Link>
        </p>

        {toast && (
          <div className="mt-4 rounded-lg border border-blue-400/30 bg-blue-500/10 px-3 py-2 text-xs text-blue-100">{toast}</div>
        )}
      </motion.section>
    </main>
  );
}
