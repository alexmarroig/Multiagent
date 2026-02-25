'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/src/lib/supabase';
import type { User, Session } from '@supabase/supabase-js';
import { useRouter } from 'next/navigation';

interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: 'user' | 'admin';
  created_at: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const hasMockAdminToken = () =>
    typeof window !== 'undefined' && localStorage.getItem('agentos_token') === 'mock-admin-token';

  const syncMockAdminCookie = (enabled: boolean) => {
    if (typeof document === 'undefined') return;
    if (enabled) {
      document.cookie = 'agentos_mock_admin=1; Path=/; SameSite=Lax';
      return;
    }
    document.cookie = 'agentos_mock_admin=; Path=/; Max-Age=0; SameSite=Lax';
  };

  useEffect(() => {
    const checkAuth = async () => {
      // Check for mock admin session first
      if (hasMockAdminToken()) {
        syncMockAdminCookie(true);
        const mockProfile: Profile = {
          id: 'admin-mock-id',
          email: 'admin@agentos.tech',
          full_name: 'Administrator',
          avatar_url: null,
          role: 'admin',
          created_at: new Date().toISOString()
        };
        setProfile(mockProfile);
        setUser({ id: 'admin-mock-id', email: 'admin@agentos.tech' } as any);
        setLoading(false);
        return;
      }

      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        await fetchProfile(session.user.id);
      } else {
        setLoading(false);
      }
    };

    checkAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (hasMockAdminToken()) {
        syncMockAdminCookie(true);
        return; // Don't let Supabase overwrite mock admin session
      }
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchProfile(session.user.id);
      } else {
        setProfile(null);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  async function fetchProfile(userId: string) {
    try {
      const { data } = await supabase.from('profiles').select('*').eq('id', userId).single();

      if (data) {
        setProfile(data as Profile);
      }
    } finally {
      setLoading(false);
    }
  }

  async function signUp(email: string, password: string, fullName: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName },
      },
    });

    if (error) throw error;
    return data;
  }

  async function signIn(email: string, password: string) {
    // Admin bypass for testing
    if (email === 'admin' && password === 'bianco256') {
      const mockProfile: Profile = {
        id: 'admin-mock-id',
        email: 'admin@agentos.tech',
        full_name: 'Administrator',
        avatar_url: null,
        role: 'admin',
        created_at: new Date().toISOString()
      };
      setProfile(mockProfile);
      setUser({ id: 'admin-mock-id', email: 'admin@agentos.tech' } as any);
      if (typeof window !== 'undefined') {
        localStorage.setItem('agentos_token', 'mock-admin-token');
      }
      syncMockAdminCookie(true);
      router.push('/agentos');
      return { user: { id: 'admin-mock-id' }, session: {} };
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;
    router.push('/agentos');
    return data;
  }

  async function signOut() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('agentos_token');
    }
    syncMockAdminCookie(false);
    await supabase.auth.signOut();
    router.push('/login');
  }

  return {
    user,
    profile,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    isAdmin: profile?.role === 'admin',
  };
}
