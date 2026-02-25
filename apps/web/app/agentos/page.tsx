'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import AgentCanvas from '@/components/agentos/AgentCanvas';
import AgentConfig from '@/components/agentos/AgentConfig';
import AgentSidebar from '@/components/agentos/AgentSidebar';
import { healthCheck } from '@/lib/api';
import { useCanvasStore } from '@/hooks/useCanvasStore';
import { useAuth } from '@/hooks/useAuth';

export default function AgentOSPage() {
  const backendOnline = useCanvasStore((s) => s.backendOnline);
  const setBackendOnline = useCanvasStore((s) => s.setBackendOnline);
  const saveFlow = useCanvasStore((s) => s.saveFlow);
  const { profile, signOut } = useAuth();

  useEffect(() => {
    healthCheck().then((isOnline) => setBackendOnline(isOnline));
  }, [setBackendOnline]);

  async function handleSave() {
    const name = window.prompt('DEPLOYMENT_IDENTIFIER:');
    if (!name) return;
    await saveFlow(name);
  }

  return (
    <div className="dark">
      <div className="flex h-screen flex-col bg-black text-white selection:bg-cyber-cyan selection:text-black">
        {/* Persistent HUD Header */}
        <header className="flex h-16 items-center justify-between border-b border-white/5 bg-black/80 backdrop-blur-xl px-6 relative z-50">
          <div className="flex items-center gap-6">
            <Link href="/" className="group flex items-center gap-2">
              <div className="h-6 w-6 border-2 border-cyber-cyan flex items-center justify-center font-black text-[10px] text-cyber-cyan group-hover:bg-cyber-cyan group-hover:text-black transition-all">
                OS
              </div>
              <span className="text-xl font-black tracking-tighter text-white uppercase italic group-hover:neon-text-cyan transition-all hidden md:block">
                Agent<span className="text-cyber-cyan">OS</span>
              </span>
            </Link>

            <div className="h-8 w-px bg-white/10 hidden md:block" />

            <div className="hidden lg:block">
              <div className="flex items-center gap-2 mb-0.5">
                <div className={`h-1.5 w-1.5 rounded-full ${backendOnline ? 'bg-cyber-cyan shadow-[0_0_5px_#00f3ff]' : 'bg-red-500 shadow-[0_0_5px_#ff0033]'}`} />
                <span className="text-[10px] font-mono tracking-widest text-neutral-500 uppercase">
                  CONNECTION_STATUS: {backendOnline ? 'ENCRYPTED_SYNC' : 'LINK_TERMINATED'}
                </span>
              </div>
              <p className="text-[8px] font-mono text-neutral-700 tracking-[0.2em] uppercase">
                LATENCY: 14ms // LOAD: 22% // MODE: PRODUCTION
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleSave}
              className="btn-cyber-outline !px-4 !py-1.5 !text-[10px] !border-white/20 hover:!border-cyber-cyan text-white/70"
            >
              [ BACKUP_FLOW ]
            </button>

            <div className="h-8 w-px bg-white/10" />

            {/* Profile Terminal */}
            <div className="relative group">
              <button className="flex items-center gap-3 pl-3 pr-2 py-1.5 border border-white/5 hover:bg-white/5 transition-colors">
                <div className="text-right">
                  <p className="text-[9px] font-mono text-neutral-500 leading-none mb-1">AUTH_LEVEL_4</p>
                  <p className="text-[11px] font-black tracking-tight text-white leading-none">
                    {profile?.full_name?.toUpperCase() || profile?.email?.split('@')[0].toUpperCase() || 'UNKNOWN_USER'}
                  </p>
                </div>
                <div className="w-8 h-8 border border-cyber-cyan/30 p-0.5">
                  <div className="w-full h-full bg-cyber-cyan/20 flex items-center justify-center text-[10px] font-black text-cyber-cyan">
                    {profile?.full_name?.charAt(0) || profile?.email?.charAt(0) || '?'}
                  </div>
                </div>
              </button>

              <div className="absolute right-0 mt-2 w-56 glass-panel border-cyber-cyan/30 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                <div className="p-4 space-y-3">
                  <div className="pb-3 border-b border-white/5">
                    <p className="text-[8px] font-mono text-neutral-500 mb-1 uppercase">Terminal_Identity</p>
                    <p className="text-[10px] text-white truncate font-mono">{profile?.email}</p>
                  </div>

                  <nav className="space-y-1">
                    {profile?.role === 'admin' && (
                      <Link href="/admin" className="block px-3 py-2 text-[10px] font-bold text-neutral-400 hover:text-cyber-cyan hover:bg-white/5 transition-colors uppercase">
                        &gt; SYSTEM_ADMIN_HUB
                      </Link>
                    )}
                    <Link href="/debug" className="block px-3 py-2 text-[10px] font-bold text-neutral-400 hover:text-cyber-cyan hover:bg-white/5 transition-colors uppercase">
                      &gt; DIAGNOSTICS_MODE
                    </Link>
                    <button
                      onClick={signOut}
                      className="w-full text-left px-3 py-2 text-[10px] font-black text-red-400 hover:bg-red-400/10 transition-colors uppercase"
                    >
                      &gt; TERMINATE_SESSION
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Global HUD Overlay Elements */}
        <div className="pointer-events-none fixed inset-0 z-0 opacity-20 overflow-hidden">
          <div className="scanline absolute inset-0" />
        </div>

        <div className="flex min-h-0 flex-1 relative z-10">
          <AgentSidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1">
              <AgentCanvas />
            </div>
          </div>
          <AgentConfig />
        </div>
      </div>
    </div>
  );
}
