'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await signIn(email, password);
    } catch (err: any) {
      setError(err?.message || 'ACCESS_DENIED: Invalid credentials or insufficient permissions.');
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
        <div className="absolute inset-0 bg-gradient-to-t from-cyber-cyan/5 via-transparent to-transparent" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="mb-12 text-center">
          <motion.div
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 1 }}
            className="inline-block border-2 border-cyber-cyan p-3 mb-6 shadow-[0_0_15px_#00f3ff]"
          >
            <span className="text-cyber-cyan text-2xl font-black">OS</span>
          </motion.div>
          <h1 className="text-2xl font-black tracking-[0.4em] text-white uppercase italic">Terminal_Access</h1>
          <div className="mt-3 flex items-center justify-center gap-2">
            <div className="h-px w-8 bg-cyber-cyan/30" />
            <p className="text-[10px] text-cyber-cyan/60 tracking-widest uppercase">SECURE_NEURAL_LINK_V4.0</p>
            <div className="h-px w-8 bg-cyber-cyan/30" />
          </div>
        </div>

        <div className="glass-panel-elevated p-8 md:p-10 border-white/10 relative">
          {/* Decorative corner accents */}
          <div className="absolute top-0 left-0 h-4 w-4 border-t border-l border-cyber-cyan" />
          <div className="absolute bottom-0 right-0 h-4 w-4 border-b border-r border-cyber-cyan" />

          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">IDENTITY_ID</label>
              <div className="relative group">
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@neural.link"
                  className="w-full border-b border-white/10 bg-transparent px-0 py-3 text-sm text-white placeholder:text-neutral-800 outline-none focus:border-cyber-cyan transition-colors"
                />
                <motion.div
                  initial={{ width: 0 }}
                  whileFocus={{ width: '100%' }}
                  className="absolute bottom-0 left-0 h-0.5 bg-cyber-cyan shadow-[0_0_10px_#00f3ff]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">ACCESS_CRYPT_KEY</label>
              <div className="relative group">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full border-b border-white/10 bg-transparent px-0 py-3 text-sm text-white placeholder:text-neutral-800 outline-none focus:border-cyber-cyan transition-colors"
                />
                <motion.div
                  initial={{ width: 0 }}
                  whileFocus={{ width: '100%' }}
                  className="absolute bottom-0 left-0 h-0.5 bg-cyber-cyan shadow-[0_0_10px_#00f3ff]"
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-[10px] text-red-400 border-l-2 border-red-500 pl-3 py-2 bg-red-500/5 font-mono uppercase"
              >
                CRITICAL_ERROR: {error}
              </motion.div>
            )}

            <button
              disabled={loading}
              className="btn-cyber-primary w-full py-5 text-sm font-black tracking-[0.3em]"
            >
              {loading ? 'ESTABLISHING_LINK...' : 'INITIALIZE_SESSION'}
            </button>
          </form>

          <div className="mt-10 flex flex-col gap-4 text-center">
            <Link className="text-[10px] font-bold text-neutral-500 hover:text-cyber-magenta transition-colors tracking-widest uppercase" href="/signup">
              [ REQUEST_NEW_ACCESS_ID ]
            </Link>
            <Link className="text-[10px] font-bold text-neutral-700 hover:text-white transition-colors tracking-widest uppercase" href="/">
              [ ABORT_AND_RETURN_HOME ]
            </Link>
          </div>
        </div>

        <div className="mt-8 flex justify-center gap-6 text-[8px] text-neutral-700 font-mono tracking-widest uppercase">
          <span>IP_LOGGED: 127.0.0.1</span>
          <span>NODE: EDGE_01</span>
          <span>SSL: AES_256</span>
        </div>
      </motion.div>
    </main>
  );
}
