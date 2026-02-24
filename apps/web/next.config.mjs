import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

const hasPackage = (pkg) => {
  try {
    require.resolve(pkg);
    return true;
  } catch {
    return false;
  }
};

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  webpack: (config) => {
    const fallbackAliases = {
      ...(config.resolve.alias || {}),
      '@': dirname,
      'styled-jsx': 'next/dist/compiled/styled-jsx',
    };

    if (!hasPackage('recharts')) {
      fallbackAliases.recharts = path.resolve(dirname, 'lib/stubs/recharts.tsx');
    }

    if (!hasPackage('date-fns')) {
      fallbackAliases['date-fns'] = path.resolve(dirname, 'lib/stubs/date-fns.ts');
      fallbackAliases['date-fns/locale'] = path.resolve(dirname, 'lib/stubs/date-fns-locale.ts');
      fallbackAliases['date-fns/locale$'] = path.resolve(dirname, 'lib/stubs/date-fns-locale.ts');
    }

    if (!hasPackage('@supabase/supabase-js')) {
      fallbackAliases['@supabase/supabase-js'] = path.resolve(dirname, 'lib/stubs/supabase-js.ts');
    }

    if (!hasPackage('@supabase/auth-helpers-nextjs')) {
      fallbackAliases['@supabase/auth-helpers-nextjs'] = path.resolve(
        dirname,
        'lib/stubs/supabase-auth-helpers-nextjs.ts'
      );
    }

    config.resolve.alias = fallbackAliases;
    return config;
  },
};

export default nextConfig;
