'use client';

import { motion } from 'framer-motion';

type MetricCardProps = {
  title: string;
  value: string;
  description: string;
};

export function MetricCard({ title, value, description }: MetricCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="rounded-xl bg-neutralDark-200 border border-neutralDark-300 p-6 shadow-md transition-all duration-300 ease-out transform hover:scale-105 hover:border-primary/60"
    >
      <h3 className="text-sm text-neutral-300">{title}</h3>
      <h2 className="mt-3 text-3xl font-bold text-neutral-100">{value}</h2>
      <p className="mt-2 text-sm text-neutral-400">{description}</p>
    </motion.article>
  );
}
