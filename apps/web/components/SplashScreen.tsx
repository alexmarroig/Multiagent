'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

export default function SplashScreen() {
  const [isVisible, setIsVisible] = useState(true);
  const [loadingText, setLoadingText] = useState('INITIALIZING AGENT_OS...');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const texts = [
      'BOOTING CORE_SYSTEM...',
      'CONNECTING TO NEURAL_NETWORK...',
      'LOADING MULTI_AGENT_PROTOCOLS...',
      'ESTABLISHING SECURE_CONNECTION...',
      'SYSTEMS_READY'
    ];

    let current = 0;
    const interval = setInterval(() => {
      if (current < texts.length - 1) {
        current++;
        setLoadingText(texts[current]);
        setProgress((prev) => prev + 25);
      } else {
        setProgress(100);
        clearInterval(interval);
        setTimeout(() => setIsVisible(false), 800);
      }
    }, 600);

    return () => clearInterval(interval);
  }, []);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{
            opacity: 0,
            scale: 1.1,
            filter: 'blur(10px)'
          }}
          transition={{ duration: 0.8, ease: 'easeInOut' }}
          className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-black"
        >
          <div className="cyber-grid absolute inset-0 opacity-20" />

          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="relative mb-12"
          >
            {/* Logo placeholder / Icon */}
            <div className="relative h-32 w-32">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 rounded-none border-2 border-cyber-cyan shadow-[0_0_15px_#00f3ff]"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
                className="absolute inset-4 rounded-none border border-cyber-magenta shadow-[0_0_15px_#ff00ff]"
              />
              <div className="flex h-full w-full items-center justify-center">
                <span className="text-3xl font-black text-white italic tracking-tighter">AGENT<span className="text-cyber-cyan">OS</span></span>
              </div>
            </div>
          </motion.div>

          <div className="w-80">
            <div className="mb-2 flex justify-between text-[10px] font-mono text-cyber-cyan">
              <span className="animate-pulse">LOAD_PROGRESS</span>
              <span>{progress}%</span>
            </div>
            <div className="h-[2px] w-full overflow-hidden bg-white/5">
              <motion.div
                initial={{ x: '-100%' }}
                animate={{ x: `${progress - 100}%` }}
                transition={{ duration: 0.5 }}
                className="h-full w-full bg-cyber-cyan shadow-[0_0_10px_#00f3ff]"
              />
            </div>
            <motion.p
              key={loadingText}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 text-center font-mono text-[10px] tracking-[0.4em] text-cyber-cyan/70 uppercase"
            >
              {loadingText}
            </motion.p>
          </div>

          <div className="scanline absolute inset-0 pointer-events-none" />

          <div className="absolute bottom-10 font-mono text-[8px] text-neutral-800 tracking-[1em] uppercase">
            Encrypted_Kernel_v4.0.1
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
