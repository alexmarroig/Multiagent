'use client';

import { motion } from 'framer-motion';

const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.55, ease: 'easeOut' },
};

export function HeroSection() {
  return (
    <section className="py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div {...reveal} className="max-w-4xl">
          <p className="inline-flex items-center rounded-full border border-primary/35 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
            Infraestrutura institucional de inteligência financeira
          </p>
          <h1 className="mt-6 text-4xl md:text-5xl font-semibold tracking-tight text-neutral-100">
            Decisões patrimoniais orientadas por dados, risco e execução em uma única experiência.
          </h1>
          <p className="mt-5 text-lg font-medium text-neutral-300">
            Unifique mercado, estratégia e governança com uma interface tecnológica, dinâmica e pronta para escalar.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
