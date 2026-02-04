import { createServerSupabaseClient } from '@/lib/supabase-server';
import { NextResponse } from 'next/server';

export async function GET(req: Request, { params }: { params: { taskId: string } }) {
  const supabase = createServerSupabaseClient();
  const { data, error } = await supabase
    .from('task_logs')
    .select('*')
    .eq('task_id', params.taskId)
    .order('id', { ascending: true });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}
