import { motion } from 'framer-motion';
import { WealthCurveChart } from '@/components/charts/WealthCurveChart';

const wealthData = [
  { month: 'Jan', patrimonio: 100 },
  { month: 'Fev', patrimonio: 112 },
  { month: 'Mar', patrimonio: 109 },
  { month: 'Abr', patrimonio: 121 },
  { month: 'Mai', patrimonio: 130 },
  { month: 'Jun', patrimonio: 138 },
  { month: 'Jul', patrimonio: 147 },
];

export function VisualExperienceSection() {
  return (
    <section id="experiencia" className="mx-auto w-full max-w-7xl px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.35 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <h2 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">Experiência visual desenhada para decisão</h2>
        <p className="mt-3 text-lg font-medium text-neutral-300">Curva de patrimônio interativa para leitura rápida da evolução financeira.</p>
      </motion.div>

      <div className="mt-8">
        <WealthCurveChart data={wealthData} />
      </div>
    </section>
  );
}
