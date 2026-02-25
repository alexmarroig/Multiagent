'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.3,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 40, filter: 'blur(10px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.8, ease: [0.2, 0.65, 0.3, 0.9] }
  },
};

export function HeroSection() {
  return (
    <section className="relative overflow-hidden py-24 md:py-32 min-h-[90vh] flex items-center">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="container relative z-10 mx-auto px-6"
      >
        <div className="content-center">
          <motion.div
            variants={itemVariants}
            className="mb-8 inline-block rounded-none border border-cyber-cyan/30 bg-cyber-cyan/5 px-4 py-1 font-mono text-[10px] uppercase tracking-[0.3em] text-cyber-cyan neon-border-cyan"
          >
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="mr-2"
            >
              ●
            </motion.span>
            System initialized: Agent_OS v4.0.1
          </motion.div>

          <motion.h1
            variants={itemVariants}
            whileHover={{ skewX: -2 }}
            className="title-cyber leading-[1.1] mb-6 cursor-default group"
          >
            A Próxima Evolução da <br />
            <span className="text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] group-hover:neon-text-cyan transition-all">Inteligência Autônoma</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="mb-12 max-w-2xl text-lg font-light leading-relaxed text-neutral-400 md:text-xl"
          >
            Construa, implante e dimensione frotas de agentes IA com infraestrutura
            de nível militar. Decisões complexas em milissegundos.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="flex flex-wrap justify-center gap-6"
          >
            <Link href="/signup" className="btn-cyber-primary group relative overflow-hidden">
              <span className="relative z-10">INICIALIZAR_PROTOCOLO</span>
              <motion.div
                className="absolute inset-0 bg-white/20 translate-x-[-100%]"
                whileHover={{ translateX: '100%' }}
                transition={{ duration: 0.5 }}
              />
            </Link>
            <Link href="/login" className="btn-cyber-outline !text-cyber-magenta !border-cyber-magenta hover:!bg-cyber-magenta/10">
              ACESSAR_TERMINAL
            </Link>
          </motion.div>

          <motion.div
            variants={containerVariants}
            className="mt-20 grid w-full max-w-5xl grid-cols-1 gap-8 md:grid-cols-3"
          >
            {[
              { label: 'Uptime do Sistema', value: '99.999%', detail: 'REDE NEURAL ATIVA', color: 'cyber-cyan' },
              { label: 'Latência Global', value: '< 12ms', detail: 'BAIXA RESPOSTA', color: 'cyber-magenta' },
              { label: 'Agentes Ativos', value: '1.2M+', detail: 'PROCESSAMENTO SYNC', color: 'cyber-yellow' },
            ].map((stat, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                whileHover={{ scale: 1.05, translateY: -5 }}
                className="glass-panel p-6 text-left border-l-2 border-l-cyber-cyan group cursor-crosshair"
              >
                <p className="font-mono text-[10px] uppercase tracking-widest text-cyber-cyan/60 group-hover:text-cyber-cyan transition-colors">{stat.label}</p>
                <p className="mt-2 text-3xl font-black text-white">{stat.value}</p>
                <div className="mt-4 h-1 w-full bg-white/5 overflow-hidden">
                   <motion.div
                     initial={{ width: 0 }}
                     whileInView={{ width: '70%' }}
                     transition={{ delay: 0.5 + (i * 0.1), duration: 1 }}
                     className="h-full bg-cyber-cyan shadow-[0_0_10px_#00f3ff]"
                   />
                </div>
                <p className="mt-2 font-mono text-[8px] text-cyber-cyan/40">{stat.detail}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Background Decorative Elements */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.1, 0.15, 0.1]
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 left-0 -translate-x-1/2 w-[500px] h-[500px] bg-cyber-cyan/20 rounded-full blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.1, 0.15, 0.1]
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-1/4 right-0 translate-x-1/2 w-[500px] h-[500px] bg-cyber-magenta/20 rounded-full blur-[120px] pointer-events-none"
      />
    </section>
  );
}
