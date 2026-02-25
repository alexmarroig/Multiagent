'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export function CallToActionSection() {
  return (
    <section className="py-16 border-t border-neutralDark-300">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 22 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="rounded-3xl border border-neutralDark-300 bg-neutralDark-200 p-8 md:p-12 text-center shadow-md"
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-neutral-100">
            Pronto para operar com clareza institucional?
          </h2>
          <p className="mt-4 text-lg font-medium text-neutral-300 max-w-2xl mx-auto">
            Eleve a tomada de decisão financeira com tecnologia de ponta, visual premium e governança contínua.
          </p>
          <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.3 }} className="mt-9 inline-block">
            <Link
              href="/signup"
              aria-label="Começar agora no AgentOS"
              className="inline-flex items-center gap-2 rounded-xl border border-primary/40 bg-gradient-to-r from-primary via-indigo-500 to-purple-600 px-7 py-3.5 text-sm font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_12px_30px_rgba(58,130,247,0.35)] transition-all duration-300 ease-out hover:scale-[1.02] hover:border-indigo-300"
            >
              Começar agora
              <span aria-hidden>→</span>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
