'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const highlights = [
  { label: 'Rentabilidade consolidada', value: '+18,42% a.a.' },
  { label: 'Risco da carteira', value: 'Moderado +' },
  { label: 'Objetivos monitorados', value: '12 metas ativas' },
];

const features = [
  {
    title: 'Painel tecnológico',
    description: 'Dashboard com visão de patrimônio, evolução mensal e alertas em tempo real em uma única tela.',
  },
  {
    title: 'Inteligência para investimentos',
    description: 'A IA do AgentOS cruza perfil de risco, cenário macro e oportunidades para sugerir próximos movimentos.',
  },
  {
    title: 'Automação de estratégia',
    description: 'Configure regras para rebalancear ativos, acompanhar metas e executar tarefas sem esforço manual.',
  },
];

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
    <main className="kinvo-shell min-h-screen text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-4 py-10 md:px-8 md:py-16">
        <header className="kinvo-glass rounded-3xl p-6 md:p-10">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div className="max-w-3xl space-y-4">
              <span className="inline-flex items-center rounded-full border border-cyan-300/60 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">
                Finanças com IA
              </span>
              <h1 className="text-4xl font-semibold leading-tight text-white md:text-6xl">
                AgentOS Vision
                <span className="block bg-gradient-to-r from-cyan-300 to-blue-500 bg-clip-text text-transparent">
                  Design inspirado no estilo Kinvo
                </span>
              </h1>
              <p className="max-w-2xl text-base text-slate-300 md:text-lg">
                Um frontend com estética tecnológica para controlar patrimônio, metas e automações financeiras com clareza.
              </p>
            </div>

            <div className="kinvo-card w-full max-w-sm rounded-2xl p-5">
              <p className="mb-4 text-sm uppercase tracking-[0.16em] text-cyan-200/80">Resumo inteligente</p>
              <div className="space-y-3">
                {highlights.map((item) => (
                  <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.14em] text-slate-400">{item.label}</p>
                    <p className="mt-1 text-lg font-semibold text-cyan-200">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/signup"
              className="rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110"
            >
              Começar agora
            </Link>
            <Link
              href="/login"
              className="rounded-xl border border-cyan-300/40 bg-white/5 px-6 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/10"
            >
              Entrar na conta
            </Link>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {features.map((feature) => (
            <article key={feature.title} className="kinvo-card rounded-2xl p-6">
              <div className="mb-4 h-1.5 w-14 rounded-full bg-gradient-to-r from-cyan-300 to-blue-500" />
              <h2 className="mb-3 text-xl font-semibold text-white">{feature.title}</h2>
              <p className="text-sm leading-relaxed text-slate-300">{feature.description}</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
