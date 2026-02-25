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
      whileHover={{ y: -5, scale: 1.02 }}
      className="relative overflow-hidden glass-panel p-8 border-l-4 border-l-cyber-cyan"
    >
      <div className="absolute top-0 right-0 p-2 opacity-10">
        <div className="h-12 w-12 border-t border-r border-white" />
      </div>

      <h3 className="font-mono text-[10px] uppercase tracking-[0.3em] text-cyber-cyan/60 mb-2">{title}</h3>
      <h2 className="text-4xl font-black text-white tracking-tighter mb-4">{value}</h2>
      <p className="text-sm font-light text-neutral-400 leading-relaxed">{description}</p>

      <div className="mt-6 flex gap-1">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-1 w-4 bg-white/5" />
        ))}
      </div>
    </motion.article>
  );
}
