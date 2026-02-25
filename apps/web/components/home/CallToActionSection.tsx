import Link from 'next/link';
import { motion } from 'framer-motion';

export function CallToActionSection() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.35 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="rounded-2xl border border-neutralDark-300 bg-gradient-to-b from-neutralDark-100 via-neutralDark-200 to-neutralDark-100 p-10 text-center shadow-md"
      >
        <h2 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
          A próxima decisão financeira pode ser a mais precisa da sua operação.
        </h2>
        <p className="mx-auto mt-4 max-w-3xl text-lg font-medium text-neutral-300">
          Entre no padrão AgentOS e transforme leitura de risco em vantagem competitiva.
        </p>
        <Link
          href="/signup"
          aria-label="Começar agora"
          className="mt-8 inline-flex rounded-xl bg-gradient-to-r from-primary via-blue-500 to-violet-500 px-8 py-3 text-sm font-semibold text-white shadow-md shadow-primary/30 transition-all duration-300 ease-out hover:scale-[1.02] hover:shadow-lg"
          style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.25), 0 8px 24px rgba(58,130,247,0.35)' }}
        >
          Começar agora
        </Link>
      </motion.div>
    </section>
  );
}
