import './globals.css';
import type { Metadata } from 'next';
import SplashScreen from '@/components/SplashScreen';

export const metadata: Metadata = {
  title: 'Agentic Dev Studio | AgentOS',
  description: 'Commercial AI Agent Monorepo - Autonomous Multi-Agent Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="overflow-x-hidden bg-black text-white selection:bg-cyber-cyan selection:text-black font-sans antialiased">
        <div className="scanline" />
        <div className="fixed inset-0 cyber-grid opacity-[0.03] pointer-events-none" />
        <SplashScreen />
        <div className="min-h-screen w-full relative z-0">
          {children}
        </div>
      </body>
    </html>
  );
}
