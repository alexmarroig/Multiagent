import { motion } from 'framer-motion';
import { MetricCard } from './MetricCard';

const metrics = [
  {
    title: 'Retorno anualizado',
    value: '18.42%',
    description: 'Performance consolidada em múltiplas estratégias.',
  },
  {
    title: 'Risco monitorado',
    value: '73/100',
    description: 'Cobertura quantitativa ativa para eventos de mercado.',
  },
  {
    title: 'Objetivos ativos',
    value: '12',
    description: 'Planos patrimoniais com acompanhamento contínuo.',
  },
  {
    title: 'Alertas críticos',
    value: '34',
    description: 'Sinais priorizados para ação imediata do time.',
  },
];

export function MetricsSection() {
  return (
    <section id="metricas" className="mx-auto w-full max-w-7xl px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.35 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <h2 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">Métricas estratégicas</h2>
        <p className="mt-3 text-lg font-medium text-neutral-300">Indicadores de performance e risco para decisões com confiança.</p>
      </motion.div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>
    </section>
  );
}
