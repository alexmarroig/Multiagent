'use client';

import { motion } from 'framer-motion';
import { WealthCurveChart, WealthCurvePoint } from '@/components/charts/WealthCurveChart';

const wealthCurveData: WealthCurvePoint[] = [
  { month: 'Jan', patrimonio: 120 },
  { month: 'Fev', patrimonio: 128 },
  { month: 'Mar', patrimonio: 124 },
  { month: 'Abr', patrimonio: 136 },
  { month: 'Mai', patrimonio: 149 },
  { month: 'Jun', patrimonio: 155 },
  { month: 'Jul', patrimonio: 168 },
  { month: 'Ago', patrimonio: 173 },
  { month: 'Set', patrimonio: 182 },
  { month: 'Out', patrimonio: 194 },
  { month: 'Nov', patrimonio: 208 },
  { month: 'Dez', patrimonio: 220 },
];

export function VisualExperienceSection() {
  return (
    <section className="py-16 border-t border-neutralDark-300">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="lg:col-span-4"
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-neutral-100">Curva de patrimônio</h2>
          <p className="mt-4 text-lg font-medium text-neutral-300">
            Visualização interativa com leitura contínua da evolução patrimonial e contexto de execução.
          </p>
          <p className="mt-3 text-sm text-neutral-400">Passe o cursor no gráfico para analisar valores mensais e tendência de performance.</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45, delay: 0.08 }}
          className="lg:col-span-8"
        >
          <WealthCurveChart data={wealthCurveData} />
        </motion.div>
      </div>
    </section>
  );
}
