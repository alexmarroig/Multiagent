import { NextResponse } from 'next/server';

export async function POST(req: Request, { params }: { params: { taskId: string } }) {
  const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8001';
  try {
    const response = await fetch(`${orchestratorUrl}/tasks/${params.taskId}/execute`, {
      method: 'POST',
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
