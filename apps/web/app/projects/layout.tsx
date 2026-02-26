import Link from 'next/link';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <aside className="w-64 bg-neutral-950/95 border-r border-neutral-800 flex flex-col backdrop-blur-md sticky inset-y-0 left-0">
        <div className="p-6 border-b border-neutral-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-5 w-5 border border-cyber-cyan flex items-center justify-center font-black text-[8px] text-cyber-cyan">
              OS
            </div>
            <span className="font-black italic uppercase tracking-tighter text-white">AgentOS</span>
          </div>
          <p className="text-[10px] font-mono text-neutral-600 tracking-widest uppercase">PROJECT_STUDIO_V1</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 font-medium overflow-y-auto">
          <Link 
            href="/projects" 
            className="block p-3 text-sm text-neutral-300 hover:bg-neutral-900 hover:text-cyber-cyan hover:border-l-2 hover:border-cyber-cyan transition-all rounded-l pl-3"
          >
            PROJECTS
          </Link>
          <Link 
            href="/connections" 
            className="block p-3 text-sm text-neutral-300 hover:bg-neutral-900 hover:text-cyber-cyan hover:border-l-2 hover:border-cyber-cyan transition-all rounded-l pl-3"
          >
            CONNECTIONS
          </Link>
        </nav>
        
        <div className="p-4 border-t border-neutral-800">
          <Link 
            href="/login" 
            className="text-sm text-neutral-500 hover:text-cyber-cyan transition-colors font-mono uppercase tracking-widest"
          >
            [ LOGOUT ]
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-black/50">
        <div className="mx-auto w-full max-w-7xl h-full">
          {children}
        </div>
      </main>
    </div>
  );
}