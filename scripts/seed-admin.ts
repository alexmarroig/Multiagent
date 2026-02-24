import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !serviceRoleKey) {
  throw new Error('Defina NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY para executar o seed.');
}

const supabase = createClient(supabaseUrl, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function ensureAdmin() {
  const adminEmail = 'admin@admin.com';
  const adminPassword = 'bianco256';

  const { data: usersData, error: usersError } = await supabase.auth.admin.listUsers();
  if (usersError) throw usersError;

  let adminUser = usersData.users.find((user) => user.email === adminEmail);

  if (!adminUser) {
    const { data, error } = await supabase.auth.admin.createUser({
      email: adminEmail,
      password: adminPassword,
      email_confirm: true,
      user_metadata: { full_name: 'Administrador AgentOS' },
    });

    if (error) throw error;
    adminUser = data.user;
    console.log('Usuário admin criado.');
  } else {
    console.log('Usuário admin já existe.');
  }

  const { error: profileError } = await supabase
    .from('profiles')
    .upsert(
      {
        id: adminUser.id,
        email: adminEmail,
        full_name: 'Administrador AgentOS',
        role: 'admin',
      },
      { onConflict: 'id' }
    );

  if (profileError) throw profileError;
  console.log('Perfil admin garantido com role=admin.');
}

ensureAdmin().catch((error) => {
  console.error(error);
  process.exit(1);
});
