'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { TopBar } from '@/components/home/TopBar';
import { HeroSection } from '@/components/home/HeroSection';
import { MetricsSection } from '@/components/home/MetricsSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { VisualExperienceSection } from '@/components/home/VisualExperienceSection';
import { CallToActionSection } from '@/components/home/CallToActionSection';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/agentos');
    }
  }, [loading, router, user]);

  if (loading) {
    return null;
  }

  return (
    <div className="relative min-h-screen bg-black text-white selection:bg-cyber-cyan selection:text-black">
      {/* Background HUD Layers */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="cyber-grid absolute inset-0 opacity-10" />
        <div className="scanline absolute inset-0 opacity-10" />
        <div className="absolute inset-0 bg-gradient-to-b from-black via-transparent to-black" />
      </div>

      <div className="relative z-10">
        <TopBar />

        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <HeroSection />

          <div className="relative">
            {/* Transition decor */}
            <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 h-2 w-2 rounded-full bg-cyber-cyan shadow-[0_0_10px_#00f3ff]" />
          </div>

          <MetricsSection />
          <FeaturesSection />
          <VisualExperienceSection />
          <CallToActionSection />
        </motion.main>

        <footer className="border-t border-white/5 py-12 bg-black/40 backdrop-blur-md">
          <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex flex-col items-center md:items-start">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-5 w-5 border border-cyber-cyan flex items-center justify-center font-black text-[8px] text-cyber-cyan">OS</div>
                <span className="font-black italic uppercase tracking-tighter text-white">AgentOS</span>
              </div>
              <p className="text-[10px] font-mono text-neutral-600 tracking-widest text-center md:text-left">
                AUTONOMOUS_OPERATING_SYSTEM_V4.0.1<br />
                BUILT_FOR_THE_NEXT_GEN_INTELLIGENCE
              </p>
            </div>

            <div className="flex gap-12 text-[10px] font-bold tracking-[0.2em] text-neutral-500 uppercase">
              <div className="flex flex-col gap-3">
                <span className="text-white">RESOURCES</span>
                <Link href="#" className="hover:text-cyber-cyan transition-colors">Documentation</Link>
                <Link href="#" className="hover:text-cyber-cyan transition-colors">API_Reference</Link>
              </div>
              <div className="flex flex-col gap-3">
                <span className="text-white">SYSTEM</span>
                <Link href="#" className="hover:text-cyber-cyan transition-colors">Status</Link>
                <Link href="#" className="hover:text-cyber-cyan transition-colors">Security</Link>
              </div>
            </div>

            <div className="text-right">
              <p className="text-[8px] font-mono text-neutral-700 uppercase mb-2">LOCAL_TIME: {new Date().toLocaleTimeString()}</p>
              <div className="flex gap-2 justify-center md:justify-end">
                <div className="h-1 w-8 bg-cyber-cyan" />
                <div className="h-1 w-4 bg-cyber-magenta" />
                <div className="h-1 w-2 bg-cyber-yellow" />
              </div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <p className="text-[10px] font-mono text-neutral-800 uppercase tracking-[0.5em]">
              © 2026 AGENT_OS_FOUNDATION // ALL_RIGHTS_RESERVED
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
