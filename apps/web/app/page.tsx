'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { TopBar } from '@/components/home/TopBar';
import { HeroSection } from '@/components/home/HeroSection';
import { MetricsSection } from '@/components/home/MetricsSection';
import { FeaturesSection } from '@/components/home/FeaturesSection';
import { VisualExperienceSection } from '@/components/home/VisualExperienceSection';
import { CallToActionSection } from '@/components/home/CallToActionSection';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/agentos');
    }
  }, [loading, router, user]);

  if (loading) return null;

  return (
    <main className="min-h-screen bg-neutralDark-100 text-neutral-100">
      <TopBar />
      <HeroSection />
      <MetricsSection />
      <FeaturesSection />
      <VisualExperienceSection />
      <CallToActionSection />
    </main>
  );
}
