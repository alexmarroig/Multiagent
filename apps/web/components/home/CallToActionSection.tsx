'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export function CallToActionSection() {
  return (
    <section className="relative mx-auto w-full max-w-7xl px-6 py-24">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        className="relative overflow-hidden rounded-none border border-cyber-cyan/30 bg-black p-12 text-center md:p-20"
      >
        {/* Animated Scanner Background */}
        <motion.div
          animate={{ translateY: ['-100%', '100%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
          className="absolute inset-x-0 h-1/2 bg-gradient-to-b from-transparent via-cyber-cyan/10 to-transparent pointer-events-none"
        />

        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="mb-6 flex justify-center"
          >
            <span className="rounded-full border border-cyber-cyan/50 px-4 py-1 font-mono text-[10px] uppercase tracking-widest text-cyber-cyan">
              Protocolo de Acesso: Ativo
            </span>
          </motion.div>

          <h2 className="title-cyber !text-4xl md:!text-6xl mb-6">
            Pronto para o <span className="text-white">Futuro Autônomo?</span>
          </h2>

          <p className="mx-auto max-w-2xl text-lg font-light leading-relaxed text-neutral-400">
            A próxima decisão pode ser a mais precisa da sua operação.
            Entre no ecossistema AgentOS e escale sua inteligência.
          </p>

          <div className="mt-12 flex flex-col items-center justify-center gap-6 sm:flex-row">
            <Link
              href="/signup"
              className="btn-cyber-primary px-12 py-4 text-base"
            >
              INICIALIZAR_CONEXÃO
            </Link>
            <Link
              href="/login"
              className="btn-cyber-outline !text-white !border-white/20 hover:!border-cyber-cyan px-12 py-4 text-base"
            >
              VISUALIZAR_DEMO
            </Link>
          </div>
        </div>

        {/* Decorative corner pieces */}
        <div className="absolute top-0 left-0 h-8 w-8 border-t-2 border-l-2 border-cyber-cyan" />
        <div className="absolute top-0 right-0 h-8 w-8 border-t-2 border-r-2 border-cyber-cyan" />
        <div className="absolute bottom-0 left-0 h-8 w-8 border-b-2 border-l-2 border-cyber-cyan" />
        <div className="absolute bottom-0 right-0 h-8 w-8 border-b-2 border-r-2 border-cyber-cyan" />
      </motion.div>

      <div className="mt-12 text-center font-mono text-[10px] text-neutral-600 tracking-widest">
        SECURE_ENCRYPTION_AES_256 // END_TO_END_SYNC // AGENT_OS_CORE
      </div>
    </section>
  );
}
