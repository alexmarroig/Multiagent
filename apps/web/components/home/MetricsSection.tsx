'use client';

import { motion } from 'framer-motion';
import { MetricCard } from './MetricCard';

const metrics = [
  {
    title: 'RETORNO_ALPHA',
    value: '18.42%',
    description: 'Performance consolidada em múltiplas estratégias neurais.',
  },
  {
    title: 'RISK_INDEX',
    value: '0.24',
    description: 'Cobertura quantitativa ativa para eventos de mercado.',
  },
  {
    title: 'ACTIVE_AGENTS',
    value: '1,284',
    description: 'Frotas de agentes operando em sincronia global.',
  },
  {
    title: 'SIGNAL_PRIORITY',
    value: 'ULTRA',
    description: 'Sinais priorizados para execução em milissegundos.',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring', damping: 15 }
  },
};

export function MetricsSection() {
  return (
    <section id="metricas" className="relative mx-auto w-full max-w-7xl px-6 py-24">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="mb-16"
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="h-1 w-1 bg-cyber-magenta" />
          <span className="font-mono text-[10px] tracking-widest text-cyber-magenta uppercase">SYSTEM_KPIs</span>
        </div>
        <h2 className="title-cyber !text-4xl md:!text-5xl">Métricas de <span className="text-white">Operação</span></h2>
      </motion.div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4"
      >
        {metrics.map((metric) => (
          <motion.div key={metric.title} variants={itemVariants}>
            <MetricCard {...metric} />
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
