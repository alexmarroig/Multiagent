'use client';

import { motion } from 'framer-motion';

const cards = [
  {
    title: 'Mercado',
    description: 'Sinais macro e micro integrados ao processo decisório com baixa latência.',
    accent: 'bg-primary',
  },
  {
    title: 'Risco',
    description: 'Modelos de exposição e compliance com gatilhos de alerta e rastreabilidade.',
    accent: 'bg-secondary',
  },
  {
    title: 'Patrimônio',
    description: 'Visão consolidada de performance e objetivos para governança executiva.',
    accent: 'bg-success',
  },
];

export function FeaturesSection() {
  return (
    <section className="py-16 border-t border-neutralDark-300">
      <div className="max-w-7xl mx-auto px-6">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-4xl md:text-5xl font-semibold tracking-tight text-neutral-100"
        >
          Camada única para mercado, risco e patrimônio
        </motion.h2>
        <p className="mt-4 text-lg font-medium text-neutral-300 max-w-3xl">
          Um framework operacional para leitura integrada, respostas rápidas e decisões com padrão institucional.
        </p>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
          {cards.map((card, index) => (
            <motion.article
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: index * 0.08 }}
              className="rounded-xl border border-neutralDark-300 bg-neutralDark-200 p-6 shadow-md transition-all duration-300 ease-out hover:scale-[1.02] hover:border-primary"
            >
              <span className={`h-1.5 w-12 rounded-full ${card.accent} block`} />
              <h3 className="mt-5 text-xl font-semibold text-neutral-100">{card.title}</h3>
              <p className="mt-3 text-sm text-neutral-400">{card.description}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
