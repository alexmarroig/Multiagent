'use client';

import { motion } from 'framer-motion';
import { WealthCurveChart } from '@/components/charts/WealthCurveChart';

const wealthData = [
  { month: '00:00', patrimonio: 100 },
  { month: '04:00', patrimonio: 112 },
  { month: '08:00', patrimonio: 109 },
  { month: '12:00', patrimonio: 121 },
  { month: '16:00', patrimonio: 130 },
  { month: '20:00', patrimonio: 138 },
  { month: '24:00', patrimonio: 147 },
];

export function VisualExperienceSection() {
  return (
    <section id="experiencia" className="relative mx-auto w-full max-w-7xl px-6 py-24">
      <div className="absolute top-0 right-0 p-8 opacity-20 hidden md:block">
        <div className="font-mono text-[10px] text-cyber-cyan text-right">
          MONITOR_ID: ALPHA_7<br />
          LOC: SECTOR_G12<br />
          STATUS: OPTIMAL
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, x: -30 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="mb-12"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="h-px w-12 bg-cyber-cyan" />
          <span className="font-mono text-xs tracking-widest text-cyber-cyan">LIVE_DATA_FEED</span>
        </div>
        <h2 className="title-cyber !text-4xl md:!text-5xl">Monitoramento <span className="text-white">Em Tempo Real</span></h2>
        <p className="mt-4 max-w-xl text-lg font-light text-neutral-400">
          Curva de processamento e evolução de ativos sincronizada com a rede neural global.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, rotateX: 10 }}
        whileInView={{ opacity: 1, scale: 1, rotateX: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 1, ease: "easeOut" }}
        className="relative group"
      >
        <div className="absolute -inset-4 bg-cyber-cyan/5 blur-xl group-hover:bg-cyber-cyan/10 transition-colors" />
        <div className="glass-panel-elevated relative overflow-hidden p-1 border-white/5">
          {/* HUD Elements overlaying the chart */}
          <div className="absolute top-4 left-4 z-10 flex gap-2">
            <div className="h-2 w-2 rounded-full bg-cyber-cyan animate-pulse" />
            <div className="h-2 w-2 rounded-full bg-cyber-magenta animate-pulse delay-75" />
            <div className="h-2 w-2 rounded-full bg-cyber-yellow animate-pulse delay-150" />
          </div>

          <div className="p-4 md:p-8 bg-black/40">
            <WealthCurveChart data={wealthData} />
          </div>

          <div className="absolute bottom-4 right-8 z-10 font-mono text-[8px] text-cyber-cyan/40">
            ENCRYPTED_DATA_STREAM_SSL_V3
          </div>
        </div>
      </motion.div>
    </section>
  );
}
