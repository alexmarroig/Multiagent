'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export function TopBar() {
  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="sticky top-0 z-40 border-b border-white/5 bg-black/60 backdrop-blur-md"
    >
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="group flex items-center gap-2">
          <div className="h-6 w-6 border-2 border-cyber-cyan flex items-center justify-center font-black text-[10px] text-cyber-cyan group-hover:bg-cyber-cyan group-hover:text-black transition-all">
            OS
          </div>
          <span className="text-xl font-black tracking-tighter text-white uppercase italic group-hover:neon-text-cyan transition-all">
            Agent<span className="text-cyber-cyan">OS</span>
          </span>
        </Link>
        <nav className="flex items-center gap-8 text-[10px] font-bold tracking-[0.2em] text-neutral-400 uppercase">
          <Link href="#metricas" className="hover:text-cyber-cyan transition-colors">
            METRICS
          </Link>
          <Link href="#experiencia" className="hover:text-cyber-cyan transition-colors">
            INTERFACE
          </Link>
          <Link href="/login" className="px-4 py-2 border border-white/10 hover:border-cyber-magenta hover:text-cyber-magenta transition-all">
            ACCESS_TERMINAL
          </Link>
        </nav>
      </div>

      {/* Scanning line for header */}
      <motion.div
        animate={{ x: ['-100%', '100%'] }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        className="h-[1px] w-1/4 bg-gradient-to-r from-transparent via-cyber-cyan/30 to-transparent absolute bottom-0"
      />
    </motion.header>
  );
}
