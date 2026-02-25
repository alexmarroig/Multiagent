import Link from 'next/link';
import { motion } from 'framer-motion';

const sectionAnimation = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.35 },
  transition: { duration: 0.5, ease: 'easeOut' },
};

export function HeroSection() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-16 md:py-24">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
        <motion.div {...sectionAnimation}>
          <p className="inline-flex items-center rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-blue-100">
            AgentOS Enterprise Financial Intelligence
          </p>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white md:text-5xl">
            Infraestrutura financeira com visão institucional e execução inteligente.
          </h1>
          <p className="mt-5 text-lg font-medium text-neutral-300">
            Mercado, risco e patrimônio em uma experiência única, construída para decisões de alto impacto.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/signup"
              aria-label="Começar agora no AgentOS"
              className="rounded-xl bg-gradient-to-r from-primary to-violet-500 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-primary/30 transition-all duration-300 ease-out hover:scale-[1.02] hover:shadow-lg"
            >
              Começar agora
            </Link>
            <Link
              href="/login"
              aria-label="Acessar plataforma"
              className="rounded-xl border border-neutralDark-300 bg-neutralDark-200 px-6 py-3 text-sm font-semibold text-neutral-100 transition-all duration-300 ease-out hover:scale-[1.02] hover:border-primary"
            >
              Ver plataforma
            </Link>
          </div>
        </motion.div>

        <motion.div
          {...sectionAnimation}
          transition={{ ...sectionAnimation.transition, delay: 0.1 }}
          className="rounded-2xl border border-neutralDark-300 bg-gradient-to-b from-neutralDark-100 via-neutralDark-200 to-neutralDark-100 p-6 shadow-md"
        >
          <p className="text-sm font-medium text-neutral-300">Cockpit institucional</p>
          <p className="mt-3 text-sm text-neutral-400">
            Painel com leitura de retorno, proteção e exposição em tempo real para operação patrimonial.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {[
              ['Retorno', '+18.4%'],
              ['Risco', '73/100'],
              ['Alertas', '34'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-neutralDark-300 bg-neutralDark-200 p-4 transition-all duration-300 ease-out hover:scale-[1.02]">
                <p className="text-xs text-neutral-400">{label}</p>
                <p className="mt-2 text-xl font-bold text-white">{value}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
