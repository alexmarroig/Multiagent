import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicRoutes = new Set(['/login', '/signup', '/']);

function isPublic(pathname: string) {
  if (publicRoutes.has(pathname)) return true;
  if (pathname.startsWith('/_next') || pathname.startsWith('/api') || pathname.includes('.')) return true;
  return false;
}

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();

  // Gracefully handle missing Supabase environment variables
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    console.warn('Supabase environment variables are missing. Bypassing auth middleware.');
    return res;
  }

  try {
    const supabase = createMiddlewareClient({ req, res });
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!isPublic(req.nextUrl.pathname) && !session) {
      return NextResponse.redirect(new URL('/login', req.url));
    }

    if (req.nextUrl.pathname.startsWith('/admin') && session) {
      const { data: profile } = await supabase.from('profiles').select('role').eq('id', session.user.id).single();

      if (profile?.role !== 'admin') {
        return NextResponse.redirect(new URL('/agentos', req.url));
      }
    }
  } catch (error) {
    console.error('Middleware auth error:', error);
  }

  return res;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
