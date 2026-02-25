import Link from 'next/link';

export function TopBar() {
  return (
    <header className="sticky top-0 z-30 border-b border-neutralDark-300 bg-neutralDark-100/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="text-sm font-semibold tracking-[0.2em] text-neutral-100" aria-label="Ir para a página inicial">
          AGENTOS
        </Link>
        <nav className="flex items-center gap-3 text-sm text-neutral-300">
          <Link href="/login" className="transition-all duration-300 ease-out hover:text-primary" aria-label="Acessar plataforma">
            Entrar
          </Link>
          <Link
            href="/signup"
            className="rounded-lg border border-primary/40 px-4 py-2 text-neutral-100 transition-all duration-300 ease-out hover:scale-[1.02] hover:border-primary"
            aria-label="Criar conta"
          >
            Criar conta
          </Link>
        </nav>
      </div>
    </header>
  );
}
