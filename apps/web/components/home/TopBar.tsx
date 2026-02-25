import Link from 'next/link';

export function TopBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-neutralDark-300/80 bg-neutralDark-100/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-white">
          AgentOS
        </Link>
        <nav className="flex items-center gap-5 text-sm text-neutral-300">
          <Link href="#metricas" className="transition-all duration-300 ease-out hover:text-white">
            Métricas
          </Link>
          <Link href="#experiencia" className="transition-all duration-300 ease-out hover:text-white">
            Experiência
          </Link>
          <Link href="/login" className="transition-all duration-300 ease-out hover:text-white">
            Entrar
          </Link>
        </nav>
      </div>
    </header>
  );
}
