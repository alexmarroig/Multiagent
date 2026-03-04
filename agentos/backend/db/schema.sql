-- Tabela de perfil de usuários (extensão de auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fluxos salvos por usuário
CREATE TABLE IF NOT EXISTS public.flows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  config JSONB NOT NULL,
  is_template BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico de execuções
CREATE TABLE IF NOT EXISTS public.executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  flow_id UUID REFERENCES public.flows(id) ON DELETE SET NULL,
  session_id TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'running' CHECK (status IN ('running', 'done', 'error')),
  config JSONB NOT NULL,
  result JSONB,
  events JSONB[],
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  duration_seconds INTEGER,
  cost_usd DECIMAL(10, 4) DEFAULT 0.00
);

-- Segredos versionados para rotação de chaves (acesso apenas service role)
CREATE TABLE IF NOT EXISTS public.secret_versions (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  value TEXT NOT NULL,
  version TEXT NOT NULL,
  is_active BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, version)
);

-- Refresh tokens persistidos de forma segura (hash)
CREATE TABLE IF NOT EXISTS public.refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  jti TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, jti)
);

-- Trilha de auditoria para acesso a runs e artefatos
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flows_user_id ON public.flows(user_id);
CREATE INDEX IF NOT EXISTS idx_flows_is_public ON public.flows(is_public) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_executions_user_id ON public.executions(user_id);
CREATE INDEX IF NOT EXISTS idx_executions_session_id ON public.executions(session_id);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON public.executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON public.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON public.refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.secret_versions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='profiles' AND policyname='Users can view own profile'
  ) THEN
    CREATE POLICY "Users can view own profile" ON public.profiles
      FOR SELECT USING (auth.uid() = id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='profiles' AND policyname='Users can insert own profile'
  ) THEN
    CREATE POLICY "Users can insert own profile" ON public.profiles
      FOR INSERT WITH CHECK (auth.uid() = id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='profiles' AND policyname='Users can update own profile'
  ) THEN
    CREATE POLICY "Users can update own profile" ON public.profiles
      FOR UPDATE USING (auth.uid() = id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='flows' AND policyname='Users can update own flows check'
  ) THEN
    CREATE POLICY "Users can update own flows check" ON public.flows
      FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='flows' AND policyname='Users can view own flows'
  ) THEN
    CREATE POLICY "Users can view own flows" ON public.flows
      FOR SELECT USING (auth.uid() = user_id OR is_public = TRUE);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='executions' AND policyname='Users can update own executions'
  ) THEN
    CREATE POLICY "Users can update own executions" ON public.executions
      FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='executions' AND policyname='Users can delete own executions'
  ) THEN
    CREATE POLICY "Users can delete own executions" ON public.executions
      FOR DELETE USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='refresh_tokens' AND policyname='Users can view own refresh tokens'
  ) THEN
    CREATE POLICY "Users can view own refresh tokens" ON public.refresh_tokens
      FOR SELECT USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='refresh_tokens' AND policyname='Users can create own refresh tokens'
  ) THEN
    CREATE POLICY "Users can create own refresh tokens" ON public.refresh_tokens
      FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='refresh_tokens' AND policyname='Users can update own refresh tokens'
  ) THEN
    CREATE POLICY "Users can update own refresh tokens" ON public.refresh_tokens
      FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='audit_logs' AND policyname='Users can view own audit logs'
  ) THEN
    CREATE POLICY "Users can view own audit logs" ON public.audit_logs
      FOR SELECT USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='audit_logs' AND policyname='Users can create own audit logs'
  ) THEN
    CREATE POLICY "Users can create own audit logs" ON public.audit_logs
      FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

-- Nenhuma policy de leitura para usuários em secret_versions; acesso somente service role.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='flows' AND policyname='Users can create own flows'
  ) THEN
    CREATE POLICY "Users can create own flows" ON public.flows
      FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='flows' AND policyname='Users can update own flows'
  ) THEN
    CREATE POLICY "Users can update own flows" ON public.flows
      FOR UPDATE USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='flows' AND policyname='Users can delete own flows'
  ) THEN
    CREATE POLICY "Users can delete own flows" ON public.flows
      FOR DELETE USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='executions' AND policyname='Users can view own executions'
  ) THEN
    CREATE POLICY "Users can view own executions" ON public.executions
      FOR SELECT USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='executions' AND policyname='Users can create own executions'
  ) THEN
    CREATE POLICY "Users can create own executions" ON public.executions
      FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS flows_updated_at ON public.flows;
CREATE TRIGGER flows_updated_at
  BEFORE UPDATE ON public.flows
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
