'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const { signIn } = useAuth();
  const [lang, setLang] = useState<'en' | 'pt'>('pt');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const t = {
    en: {
      title: 'Terminal_Access',
      subtitle: 'SECURE_NEURAL_LINK_V4.0',
      identity: 'ACCESS_ID / EMAIL',
      key: 'SECURE_ACCESS_KEY / PASSWORD',
      button: 'INITIALIZE_SESSION',
      loading: 'ESTABLISHING_LINK...',
      request: '[ REQUEST_NEW_ACCESS_ID ]',
      abort: '[ ABORT_AND_RETURN_HOME ]',
      error: 'CRITICAL_ERROR'
    },
    pt: {
      title: 'Acesso_ao_Terminal',
      subtitle: 'LINK_NEURAL_SEGURO_V4.0',
      identity: 'ID_DE_ACESSO / E-MAIL',
      key: 'CHAVE_DE_ACESSO / SENHA',
      button: 'INICIALIZAR_SESSÃO',
      loading: 'ESTABELECENDO_LINK...',
      request: '[ SOLICITAR_NOVO_ACESSO ]',
      abort: '[ ABORTAR_E_VOLTAR_INICIO ]',
      error: 'ERRO_CRITICO'
    }
  }[lang];

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

      <div className="absolute top-6 right-6 z-30 flex bg-white/5 border border-white/10 p-0.5">
        <button onClick={() => setLang('en')} className={`px-2 py-1 text-[9px] font-bold ${lang === 'en' ? 'bg-cyber-cyan text-black' : 'text-white/40'}`}>EN</button>
        <button onClick={() => setLang('pt')} className={`px-2 py-1 text-[9px] font-bold ${lang === 'pt' ? 'bg-cyber-cyan text-black' : 'text-white/40'}`}>PT</button>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-20 w-full max-w-md"
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
          <h1 className="text-2xl font-black tracking-[0.4em] text-white uppercase italic">{t.title}</h1>
          <div className="mt-3 flex items-center justify-center gap-2">
            <div className="h-px w-8 bg-cyber-cyan/30" />
            <p className="text-[10px] text-cyber-cyan/60 tracking-widest uppercase">{t.subtitle}</p>
            <div className="h-px w-8 bg-cyber-cyan/30" />
          </div>
        </div>

        <div className="glass-panel-elevated p-8 md:p-10 border-white/10 relative">
          {/* Decorative corner accents */}
          <div className="absolute top-0 left-0 h-4 w-4 border-t border-l border-cyber-cyan" />
          <div className="absolute bottom-0 right-0 h-4 w-4 border-b border-r border-cyber-cyan" />

          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">{t.identity}</label>
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
              <label className="block text-[10px] font-bold text-neutral-500 uppercase tracking-[0.2em]">{t.key}</label>
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
                {t.error}: {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-cyber-primary w-full py-5 text-sm font-black tracking-[0.3em]"
            >
              {loading ? t.loading : t.button}
            </button>
          </form>

          <div className="mt-10 flex flex-col gap-4 text-center">
            <Link className="text-[10px] font-bold text-neutral-500 hover:text-cyber-magenta transition-colors tracking-widest uppercase" href="/signup">
              {t.request}
            </Link>
            <Link className="text-[10px] font-bold text-neutral-700 hover:text-white transition-colors tracking-widest uppercase" href="/">
              {t.abort}
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
