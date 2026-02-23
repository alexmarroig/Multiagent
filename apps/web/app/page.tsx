'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { motionEase, revealMotion } from '@/src/design-system/motion';
import { theme } from '@/src/design-system/theme';

type Metric = {
  label: string;
  value: number;
  suffix: string;
  description: string;
  decimals?: number;
};

const metrics: Metric[] = [
  { label: 'Retorno anualizado', value: 18.42, suffix: '%', description: 'Resultado consolidado com leitura multiestratégia.', decimals: 2 },
  { label: 'Risco monitorado', value: 73, suffix: '/100', description: 'Cobertura quantitativa ativa em todos os mandatos.' },
  { label: 'Objetivos ativos', value: 12, suffix: '', description: 'Planejamento patrimonial acompanhado em tempo real.' },
  { label: 'Alertas críticos', value: 34, suffix: '', description: 'Sinais operacionais com contexto financeiro e prioridade.' },
];

const revealWithDelay = (delay = 0) => ({
  ...revealMotion,
  transition: { ...revealMotion.transition, delay },
});

function CountUpMetric({ metric, index }: { metric: Metric; index: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  return (
    <motion.article
      {...revealWithDelay(index * 0.08)}
      onViewportEnter={() => {
        const startedAt = performance.now();
        const duration = 1200;

        const tick = (now: number) => {
          const progress = Math.min((now - startedAt) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          setDisplayValue(metric.value * eased);
          if (progress < 1) requestAnimationFrame(tick);
        };

        requestAnimationFrame(tick);
      }}
      className="depth-2 depth-3 rounded-2xl border border-white/10 bg-white/5 p-8"
      whileHover={{ y: -6, borderColor: 'rgba(255,255,255,0.2)' }}
    >
      <p className="text-sm uppercase tracking-[0.16em]" style={{ color: theme.colors.textTertiary }}>{metric.label}</p>
      <p className="mt-4 text-3xl font-semibold text-white">
        {metric.decimals ? displayValue.toFixed(metric.decimals) : Math.round(displayValue).toString()}
        <span className="ml-1 text-base" style={{ color: theme.colors.textSecondary }}>{metric.suffix}</span>
      </p>
      <p className="mt-3 text-sm" style={{ color: theme.colors.textSecondary }}>{metric.description}</p>
    </motion.article>
  );
}

function FloatingDashboard() {
  return (
    <motion.div
      {...revealWithDelay(0.35)}
      className="depth-2 relative rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-2xl"
      style={{ boxShadow: theme.shadows.depth3 }}
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
    >
      <div className="mb-5 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.15em]" style={{ color: theme.colors.textTertiary }}>AgentOS Dashboard</p>
        <span className="rounded-full border border-white/20 px-3 py-1 text-xs text-blue-200">Live</span>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4 md:col-span-3">
          <p className="text-xs text-gray-400">Curva de patrimônio</p>
          <svg className="mt-4 h-24 w-full" viewBox="0 0 240 90" fill="none">
            <motion.path
              d="M8 78 C36 62, 65 55, 98 54 C128 53, 145 25, 178 29 C202 32, 220 14, 232 12"
              stroke="#60A5FA"
              strokeWidth="3"
              initial={{ pathLength: 0.1, opacity: 0.4 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 2.2, repeat: Infinity, repeatType: 'mirror', ease: motionEase }}
            />
          </svg>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4 md:col-span-2">
          <p className="text-xs text-gray-400">Alocação</p>
          <div className="mt-4 space-y-3">
            <div className="h-2 rounded-full bg-blue-400/80" style={{ width: '78%' }} />
            <div className="h-2 rounded-full bg-blue-300/60" style={{ width: '61%' }} />
            <div className="h-2 rounded-full bg-blue-200/45" style={{ width: '46%' }} />
          </div>
        </div>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs text-gray-400">Proteções</p>
          <p className="mt-2 text-xl font-semibold text-white drop-shadow-[0_0_14px_rgba(96,165,250,0.35)]">12 ativas</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs text-gray-400">Próxima ação</p>
          <p className="mt-2 text-xl font-semibold text-white drop-shadow-[0_0_14px_rgba(96,165,250,0.35)]">18:00 UTC-3</p>
        </div>
      </div>
    </motion.div>
  );
}

function FeatureBand({ reverse, title, description }: { reverse?: boolean; title: string; description: string }) {
  return (
    <section className="section-divider relative overflow-hidden px-6 py-24 md:px-10">
      <div className={`mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-12 md:grid-cols-12 ${reverse ? '[&>*:first-child]:md:order-2 [&>*:last-child]:md:order-1' : ''}`}>
        <motion.div {...revealMotion} className="md:col-span-5">
          <h2 className="text-3xl font-semibold tracking-tight text-white" style={{ fontSize: theme.typography.sectionTitle }}>{title}</h2>
          <p className="mt-5 text-base leading-relaxed" style={{ color: theme.colors.textSecondary }}>{description}</p>
        </motion.div>
        <motion.div {...revealWithDelay(0.14)} className="md:col-span-7">
          <FloatingDashboard />
        </motion.div>
      </div>
    </section>
  );
}

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.push('/agentos');
  }, [loading, router, user]);

  if (loading) return null;

  return (
    <main className="relative min-h-screen overflow-hidden" style={{ backgroundColor: theme.colors.backgroundPrimary }}>
      <div className="noise-overlay" />
      <div className="light-spot left-[6%] top-[6%]" />
      <div className="light-spot bottom-[4%] right-[8%]" />

      <section className="relative mx-auto grid min-h-[90vh] w-full max-w-6xl grid-cols-1 items-center gap-10 px-6 py-24 md:grid-cols-12 md:px-10">
        <div className="md:col-span-7">
          <motion.p {...revealWithDelay(0.05)} className="mb-8 text-xs uppercase tracking-[0.2em] text-blue-200">AgentOS Enterprise Financial Intelligence</motion.p>
          <motion.h1
            {...revealWithDelay(0.15)}
            className="max-w-4xl font-semibold tracking-[-0.04em] text-white"
            style={{ fontSize: theme.typography.heroTitle, lineHeight: 0.92 }}
          >
            Infraestrutura de inteligência financeira para operar com precisão institucional.
          </motion.h1>
          <motion.p {...revealWithDelay(0.26)} className="mt-8 max-w-[600px] text-base leading-relaxed text-gray-400">
            Clareza operacional, visão de risco e execução assistida por IA em uma camada única de controle patrimonial.
          </motion.p>
          <motion.div {...revealWithDelay(0.36)} className="mt-12 flex flex-wrap gap-4">
            <motion.div whileHover={{ scale: 1.04, boxShadow: theme.shadows.glow }} transition={{ duration: 0.45, ease: motionEase }}>
              <Link
                href="/signup"
                className="inline-flex rounded-[14px] border border-blue-400/30 bg-gradient-to-r from-[#3B82F6] to-[#2563EB] px-7 py-3.5 text-sm font-semibold text-white"
              >
                Ativar AgentOS
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.04 }} transition={{ duration: 0.45, ease: motionEase }}>
              <Link href="/login" className="inline-flex rounded-[14px] border border-white/15 bg-white/0 px-7 py-3.5 text-sm font-semibold text-white hover:bg-white/10">
                Ver plataforma
              </Link>
            </motion.div>
          </motion.div>
        </div>

        <div className="md:col-span-5">
          <FloatingDashboard />
        </div>
      </section>

      <section className="section-divider px-6 py-16 md:px-10">
        <div className="mx-auto grid w-full max-w-6xl grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric, index) => (
            <CountUpMetric key={metric.label} metric={metric} index={index} />
          ))}
        </div>
      </section>

      <FeatureBand title="Camada única para mercado, risco e patrimônio." description="Conecte sinais de mercado, carteira e objetivos em um cockpit consistente, projetado para decisões financeiras de alto valor." />
      <FeatureBand reverse title="Experiência visual desenhada para decisão." description="Hierarquia clara, contraste preciso e microinterações suaves para leitura instantânea em contexto institucional." />

      <section className="section-divider bg-gradient-to-b from-[#0b1320] to-[#0f172a] px-6 py-24 md:px-10">
        <motion.div {...revealMotion} className="mx-auto max-w-5xl rounded-[2rem] border border-white/10 bg-white/5 px-8 py-16 text-center backdrop-blur-md md:px-14">
          <h3 className="mx-auto max-w-4xl text-4xl font-semibold tracking-tight text-white md:text-6xl">A próxima decisão financeira pode ser a mais precisa da sua operação.</h3>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed" style={{ color: theme.colors.textSecondary }}>
            Entre no padrão AgentOS de controle, tecnologia e clareza para patrimônio de alta responsabilidade.
          </p>
          <motion.div whileHover={{ scale: 1.04, boxShadow: theme.shadows.glow }} transition={{ duration: 0.45, ease: motionEase }} className="mt-10 inline-block">
            <Link href="/signup" className="inline-flex rounded-[14px] border border-blue-400/30 bg-gradient-to-r from-[#3B82F6] to-[#2563EB] px-8 py-4 text-sm font-semibold text-white">
              Começar agora
            </Link>
          </motion.div>
        </motion.div>
      </section>
    </main>
  );
}
