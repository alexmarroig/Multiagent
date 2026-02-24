'use client';

import { motion } from 'framer-motion';

const points = [
  { x: 20, y: 180 },
  { x: 90, y: 165 },
  { x: 160, y: 138 },
  { x: 230, y: 120 },
  { x: 300, y: 98 },
  { x: 370, y: 88 },
  { x: 440, y: 70 },
  { x: 510, y: 64 },
  { x: 580, y: 52 },
];

const metrics = [
  { label: 'Liquidez imediata', value: 'R$ 14,8M', detail: '+4,2% nas últimas 24h' },
  { label: 'Exposição a risco', value: '13,4%', detail: '-1,1 p.p. vs. semana anterior' },
  { label: 'Eficiência operacional', value: '92,7%', detail: '+2,3 p.p. em 30 dias' },
];

export default function DashboardPage() {
  const path = points.map((p, index) => `${index === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
        <p className="text-xs uppercase tracking-[0.2em] text-blue-200">Patrimônio consolidado</p>
        <h1 className="mt-4 text-5xl font-semibold tracking-tight text-white">R$ 248,9M</h1>
        <p className="mt-2 text-sm text-gray-400">Visão em tempo real da operação financeira institucional.</p>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {metrics.map((metric) => (
          <article key={metric.label} className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
            <p className="text-sm text-gray-400">{metric.label}</p>
            <p className="mt-3 text-3xl font-semibold text-white">{metric.value}</p>
            <p className="mt-2 text-xs text-blue-200">{metric.detail}</p>
          </article>
        ))}
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-medium text-white">Curva patrimonial</h2>
          <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-gray-300">Atualização contínua</span>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#070b14] p-4">
          <svg viewBox="0 0 600 220" className="h-[260px] w-full" fill="none">
            <path d="M 20 200 L 580 200" stroke="rgba(148,163,184,0.25)" />
            <motion.path
              d={path}
              stroke="#60a5fa"
              strokeWidth="3"
              strokeLinecap="round"
              initial={{ pathLength: 0, opacity: 0.2 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            />
          </svg>
        </div>
      </section>
    </div>
  );
}
