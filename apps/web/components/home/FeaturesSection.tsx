import { motion } from 'framer-motion';

const features = [
  {
    title: 'Mercado em contexto',
    text: 'Sinais de mercado com filtros institucionais para leitura de cenário em segundos.',
  },
  {
    title: 'Risco sob controle',
    text: 'Alertas de drawdown, exposição e stress com priorização operacional.',
  },
  {
    title: 'Patrimônio em evolução',
    text: 'Objetivos e performance conectados em um fluxo de decisão contínuo.',
  },
];

export function FeaturesSection() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.35 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <h2 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">Camada única para mercado, risco e patrimônio</h2>
        <p className="mt-3 text-lg font-medium text-neutral-300">Uma arquitetura visual consistente para reduzir ruído e ampliar clareza.</p>
      </motion.div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
        {features.map((feature) => (
          <article
            key={feature.title}
            className="rounded-xl border border-neutralDark-300 bg-neutralDark-200 p-6 shadow-md transition-all duration-300 ease-out hover:scale-[1.02] hover:border-primary"
          >
            <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
            <p className="mt-3 text-sm text-neutral-400">{feature.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
