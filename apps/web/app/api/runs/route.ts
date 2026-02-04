import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const body = await req.json();
  const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8001';
  try {
    const response = await fetch(`${orchestratorUrl}/runs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
