import Link from 'next/link';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 text-xl font-bold border-b border-gray-800 text-blue-400">
          Agentic Studio
        </div>
        <nav className="flex-1 p-4 space-y-2 font-medium">
          <Link href="/projects" className="block p-2 hover:bg-gray-800 rounded transition">
            Projects
          </Link>
          <Link href="/connections" className="block p-2 hover:bg-gray-800 rounded transition">
            Connections
          </Link>
        </nav>
        <div className="p-4 border-t border-gray-800">
          <Link href="/login" className="text-sm text-gray-400 hover:text-white transition">Sign Out</Link>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
