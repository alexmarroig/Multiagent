'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function SignupPage() {
  const { signUp } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await signUp(email, password, fullName);
    } catch (err: any) {
      setError(err?.message || 'REGISTRATION_FAILED: System overload or invalid parameters.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-black px-4 font-mono">
      {/* Background HUD Layer */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="cyber-grid absolute inset-0 opacity-10" />
        <div className="scanline absolute inset-0 opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-t from-cyber-magenta/5 via-transparent to-transparent" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="mb-12 text-center">
          <motion.div
            initial={{ rotate: 90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 1 }}
            className="inline-block border-2 border-cyber-magenta p-3 mb-6 shadow-[0_0_15px_#ff00ff]"
          >
            <span className="text-cyber-magenta text-2xl font-black">OS</span>
          </motion.div>
          <h1 className="text-2xl font-black tracking-[0.4em] text-white uppercase italic">Agent_Registration</h1>
          <div className="mt-3 flex items-center justify-center gap-2">
            <div className="h-px w-8 bg-cyber-magenta/30" />
            <p className="text-[10px] text-cyber-magenta/60 tracking-widest uppercase">PROTOCOL_ENROLLMENT_ACTIVE</p>
            <div className="h-px w-8 bg-cyber-magenta/30" />
          </div>
        </div>

        <div className="glass-panel-elevated p-8 md:p-10 border-white/10 relative">
          {/* Decorative corner accents */}
          <div className="absolute top-0 left-0 h-4 w-4 border-t border-l border-cyber-magenta" />
          <div className="absolute bottom-0 right-0 h-4 w-4 border-b border-r border-cyber-magenta" />

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">DESIGNATION_FULL_NAME</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Agent Name"
                className="w-full border-b border-white/10 bg-transparent px-0 py-3 text-sm text-white placeholder:text-neutral-800 outline-none focus:border-cyber-magenta transition-colors"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">IDENTITY_ID_EMAIL</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="agent@neural.link"
                className="w-full border-b border-white/10 bg-transparent px-0 py-3 text-sm text-white placeholder:text-neutral-800 outline-none focus:border-cyber-magenta transition-colors"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">NEW_CRYPT_KEY</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full border-b border-white/10 bg-transparent px-0 py-3 text-sm text-white placeholder:text-neutral-800 outline-none focus:border-cyber-magenta transition-colors"
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-[10px] text-red-400 border-l-2 border-red-500 pl-3 py-2 bg-red-500/5 font-mono uppercase"
              >
                SYSTEM_FAIL: {error}
              </motion.div>
            )}

            <button
              disabled={loading}
              className="btn-cyber-outline !border-cyber-magenta !text-cyber-magenta hover:!bg-cyber-magenta/10 w-full py-5 text-sm font-black tracking-[0.3em]"
            >
              {loading ? 'GENERATING_IDENTIFIER...' : 'CREATE_PROTOCOL_LINK'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <Link className="text-[10px] font-bold text-neutral-500 hover:text-cyber-cyan transition-colors tracking-widest uppercase" href="/login">
              [ ALREADY_HAVE_ID? LOGIN_TERMINAL ]
            </Link>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
