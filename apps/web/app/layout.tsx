import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Agentic Dev Studio',
  description: 'Commercial AI Agent Monorepo',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="overflow-x-hidden bg-neutral-950 text-neutral-100">
        <div className="min-h-screen w-full">{children}</div>
      </body>
    </html>
  );
}
