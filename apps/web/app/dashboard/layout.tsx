import type { ReactNode } from 'react';
import Link from 'next/link';

const navigation = [
  { label: 'Visão geral', href: '/dashboard', active: true },
  { label: 'Operações', href: '/projects' },
  { label: 'Conexões', href: '/connections' },
  { label: 'Execuções', href: '/runs/1' },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 antialiased">
      <aside className="fixed inset-y-0 left-0 z-30 w-[240px] border-r border-neutral-800 bg-neutral-950/95 px-4 py-6 backdrop-blur">
        <div className="mb-10 px-3">
          <p className="text-xs uppercase tracking-[0.2em] text-neutral-400">AgentOS</p>
          <p className="mt-2 text-lg font-semibold tracking-tight text-neutral-100">Enterprise Console</p>
        </div>

        <nav className="space-y-1.5">
          {navigation.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium leading-5 whitespace-nowrap transition-all duration-300 ${
                item.active
                  ? 'border border-neutral-800 bg-neutral-900 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]'
                  : 'text-neutral-400 hover:border hover:border-neutral-800 hover:bg-neutral-900/80 hover:text-neutral-200'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <header className="fixed left-[240px] right-0 top-0 z-20 h-16 border-b border-neutral-800 bg-neutral-950/95 backdrop-blur">
        <div className="mx-auto flex h-full w-full max-w-7xl items-center justify-between px-6">
          <div className="min-w-0">
            <p className="text-sm text-neutral-400">Controle institucional</p>
            <p className="truncate text-lg font-medium tracking-tight text-neutral-100">Dashboard executivo</p>
          </div>
          <div className="whitespace-nowrap rounded-lg border border-emerald-900/80 bg-emerald-950/50 px-3 py-1.5 text-xs font-medium text-emerald-300">
            Live
          </div>
        </div>
      </header>

      <main className="ml-[240px] pt-16">
        <section className="h-[calc(100vh-64px)] overflow-y-auto px-6 py-6">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </section>
      </main>
    </div>
  );
}
