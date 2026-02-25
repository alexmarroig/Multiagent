'use client';

import { motion } from 'framer-motion';

const features = [
  {
    title: 'NÚCLEO NEURAL',
    text: 'Processamento de linguagem natural avançado para automação de tarefas complexas e tomada de decisão.',
    id: 'PRT_001',
    color: 'cyber-cyan'
  },
  {
    title: 'EXECUÇÃO PARALELA',
    text: 'Frotas de agentes operando em sincronia, escalando sua produtividade além dos limites humanos.',
    id: 'PRT_002',
    color: 'cyber-magenta'
  },
  {
    title: 'SEGURANÇA QUANTUM',
    text: 'Criptografia de ponta a ponta e protocolos de isolamento para garantir a integridade dos seus dados.',
    id: 'PRT_003',
    color: 'cyber-yellow'
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, x: -50, filter: 'blur(10px)' },
  visible: {
    opacity: 1,
    x: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.6, ease: "easeOut" }
  },
};

export function FeaturesSection() {
  return (
    <section className="relative mx-auto w-full max-w-7xl px-6 py-24 overflow-hidden">
      <div className="cyber-grid absolute inset-0 opacity-5 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        className="content-center mb-20"
      >
        <h2 className="title-cyber !text-4xl md:!text-5xl text-center">Protocolos de <span className="text-cyber-cyan">Alta Performance</span></h2>
        <p className="mt-6 max-w-2xl text-center text-lg font-light text-neutral-400">
          Uma arquitetura visual consistente para reduzir ruído e ampliar clareza na gestão de agentes.
        </p>
      </motion.div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-3"
      >
        {features.map((feature, idx) => (
          <motion.article
            key={feature.title}
            variants={cardVariants}
            whileHover={{
              scale: 1.05,
              rotateY: 10,
              z: 50
            }}
            className="group relative perspective-1000 cursor-pointer"
          >
            <div className="absolute -inset-[1px] bg-gradient-to-b from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="glass-panel relative p-8 h-full border-t-0 border-r-0">
              <div className="flex justify-between items-start mb-6">
                <span className="font-mono text-[10px] text-cyber-cyan/50 tracking-tighter">{feature.id}</span>
                <div className={`h-1 w-12 bg-${feature.color} shadow-[0_0_10px_currentColor]`} />
              </div>

              <h3 className="text-2xl font-black text-white tracking-tighter mb-4 group-hover:text-cyber-cyan transition-colors">
                {feature.title}
              </h3>

              <p className="text-sm font-light leading-relaxed text-neutral-400 group-hover:text-neutral-200 transition-colors">
                {feature.text}
              </p>

              <div className="mt-8 flex items-center gap-2">
                <div className="h-[1px] flex-1 bg-white/10" />
                <motion.div
                   animate={{ opacity: [0.2, 1, 0.2] }}
                   transition={{ duration: 2, repeat: Infinity }}
                   className="h-1.5 w-1.5 rounded-full bg-cyber-cyan shadow-[0_0_5px_#00f3ff]"
                />
              </div>
            </div>
          </motion.article>
        ))}
      </motion.div>
    </section>
  );
}
