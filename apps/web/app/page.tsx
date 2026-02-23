'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useRef, useState } from 'react';

type Metric = {
  label: string;
  value: number;
  suffix: string;
  description: string;
  decimals?: number;
};

const metrics: Metric[] = [
  { label: 'Rentabilidade', value: 18.42, suffix: '% a.a.', description: 'Performance consolidada em múltiplas estratégias.', decimals: 2 },
  { label: 'Risco', value: 73, suffix: '/100', description: 'Leitura quantitativa com proteção dinâmica.' },
  { label: 'Metas', value: 12, suffix: ' ativas', description: 'Objetivos de patrimônio monitorados em tempo real.' },
  { label: 'Alertas', value: 34, suffix: ' inteligentes', description: 'Sinais acionáveis com curadoria de IA financeira.' },
];

function useInView<T extends HTMLElement>(options?: IntersectionObserverInit) {
  const ref = useRef<T | null>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node || isInView) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3, ...options },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [isInView, options]);

  return { ref, isInView };
}

function CountUpMetric({ metric, index }: { metric: Metric; index: number }) {
  const { ref, isInView } = useInView<HTMLDivElement>({ rootMargin: '-80px' });
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!isInView) return;

    const duration = 1200;
    const start = performance.now();
    let frame = 0;

    const animate = (time: number) => {
      const progress = Math.min((time - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(metric.value * eased);

      if (progress < 1) frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [isInView, metric.value]);

  const formatted = useMemo(() => (metric.decimals ? current.toFixed(metric.decimals) : Math.round(current).toString()), [current, metric.decimals]);

  return (
    <article
      ref={ref}
      className={`glass-card group relative overflow-hidden rounded-2xl p-7 transition-all duration-500 ${
        isInView ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'
      }`}
      style={{ transitionDelay: `${index * 110}ms` }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/10 via-transparent to-transparent opacity-0 transition duration-300 group-hover:opacity-100" />
      <p className="relative text-sm uppercase tracking-[0.16em] text-slate-400">{metric.label}</p>
      <p className="relative mt-3 text-3xl font-bold tracking-tight text-white">
        {formatted}
        <span className="ml-1 text-base font-medium text-cyan-300">{metric.suffix}</span>
      </p>
      <p className="relative mt-4 text-sm text-slate-400">{metric.description}</p>
    </article>
  );
}

function DashboardMockup() {
  return (
    <div className="glass-card relative mx-auto w-full max-w-xl rounded-3xl p-5 md:p-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.16em] text-slate-400">AgentOS Vision</span>
        <span className="rounded-full border border-cyan-300/40 px-3 py-1 text-xs text-cyan-200">Live</span>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 md:col-span-2">
          <p className="text-xs text-slate-400">Patrimônio</p>
          <p className="mt-2 text-2xl font-semibold text-white">R$ 12,4M</p>
          <div className="mt-5 h-24 rounded-xl bg-gradient-to-r from-cyan-500/30 via-blue-500/20 to-transparent" />
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs text-slate-400">Alocação</p>
          <div className="mt-4 space-y-2">
            <div className="h-2 w-5/6 rounded-full bg-cyan-300/70" />
            <div className="h-2 w-2/3 rounded-full bg-blue-400/60" />
            <div className="h-2 w-1/2 rounded-full bg-indigo-300/40" />
          </div>
        </div>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs text-slate-400">Proteções ativas</p>
          <p className="mt-2 text-lg font-semibold text-white">12 gatilhos</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs text-slate-400">Próximo rebalanceamento</p>
          <p className="mt-2 text-lg font-semibold text-white">Hoje, 18:00</p>
        </div>
      </div>
    </div>
  );
}

function FeatureSection({ title, description, bullets, reverse }: { title: string; description: string; bullets: string[]; reverse?: boolean }) {
  const { ref, isInView } = useInView<HTMLElement>({ threshold: 0.2 });

  return (
    <section ref={ref} className="mx-auto grid w-full max-w-6xl items-center gap-10 px-6 py-20 md:grid-cols-2 md:px-8">
      <div className={`${reverse ? 'md:order-2' : ''} transition-all duration-700 ${isInView ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}>
        <h2 className="text-3xl font-semibold tracking-tight text-white md:text-4xl">{title}</h2>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-400">{description}</p>
        <ul className="mt-8 space-y-4">
          {bullets.map((bullet, index) => (
            <li
              key={bullet}
              className={`flex items-start gap-3 text-slate-300 transition-all duration-500 ${isInView ? 'translate-x-0 opacity-100' : '-translate-x-5 opacity-0'}`}
              style={{ transitionDelay: `${index * 110}ms` }}
            >
              <span className="mt-1 inline-block h-5 w-5 rounded-full border border-cyan-300/50 bg-cyan-400/15" />
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      </div>

      <div
        className={`${reverse ? 'md:order-1' : ''} transition-all duration-700 ${isInView ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}`}
        style={{ transitionDelay: '140ms' }}
      >
        <DashboardMockup />
      </div>
    </section>
  );
}

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.push('/agentos');
  }, [user, loading, router]);

  if (loading) return null;

  return (
    <main className="premium-bg min-h-screen overflow-hidden text-slate-100">
      <div className="noise-layer pointer-events-none" />
      <div className="grid-overlay pointer-events-none" />

      <section className="relative mx-auto flex min-h-[90vh] w-full max-w-6xl flex-col justify-center px-6 py-24 md:px-8">
        <div className="spotlight pointer-events-none" />

        {/* Hero hierarchy intentionally oversized for premium positioning and fast value communication. */}
        <span className="chip mb-8 w-fit animate-fade-up [animation-delay:200ms]">AgentOS VisionDesign</span>
        <h1 className="animate-fade-up max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.03em] text-white [animation-delay:350ms] md:text-7xl">
          Controle financeiro
          <span className="block text-cyan-300">com Inteligência Real</span>
        </h1>
        <p className="animate-fade-up mt-8 max-w-2xl text-lg text-slate-400 [animation-delay:500ms]">
          Automatize patrimônio, estratégia e metas com IA. Uma experiência premium para decisões de alto impacto.
        </p>

        <div className="animate-fade-up mt-10 flex flex-wrap gap-4 [animation-delay:650ms]">
          <Link href="/signup" className="btn-primary">
            Ativar AgentOS
          </Link>
          <Link href="/login" className="btn-secondary">
            Ver demonstração
          </Link>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 pb-14 md:px-8">
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric, index) => (
            <CountUpMetric key={metric.label} metric={metric} index={index} />
          ))}
        </div>
      </section>

      <FeatureSection
        title="Decisões financeiras guiadas por IA contextual"
        description="Orquestramos patrimônio, risco e cenário de mercado em uma camada única de inteligência operacional para você agir com confiança."
        bullets={[
          'Leitura de risco contínua com alertas preditivos.',
          'Recomendações adaptativas baseadas em perfil e metas.',
          'Execução automatizada com governança total de estratégia.',
        ]}
      />

      <FeatureSection
        reverse
        title="Um cockpit premium para patrimônio de alto nível"
        description="Cada tela foi desenhada para clareza absoluta: contraste elevado, hierarquia precisa e sinais visuais que aceleram decisões."
        bullets={[
          'Visual minimalista com foco em ação e não em ruído.',
          'Insights em tempo real com microinterações naturais.',
          'Arquitetura responsiva com profundidade e elegância.',
        ]}
      />

      <section className="px-6 py-24 md:px-8">
        <div className="final-cta mx-auto max-w-5xl rounded-[2rem] px-8 py-16 text-center md:px-16">
          <h3 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">Transforme estratégia em resultado.</h3>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300">
            Entre para o padrão de gestão financeira que combina precisão institucional, IA e design de produto de elite.
          </p>
          <Link href="/signup" className="btn-primary mx-auto mt-10 inline-flex text-base">
            Começar agora
          </Link>
        </div>
      </section>
    </main>
  );
}
