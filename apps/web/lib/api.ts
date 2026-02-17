const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function getAuthHeaders(): HeadersInit {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem('agentos_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface NodePayload {
  id: string;
  agent_type: string;
  label: string;
  model: string;
  provider: string;
  system_prompt: string;
  tools: string[];
}

export interface EdgePayload {
  id: string;
  source: string;
  target: string;
}

export interface FlowPayload {
  session_id: string;
  nodes: NodePayload[];
  edges: EdgePayload[];
  inputs: Record<string, unknown>;
}

export interface RunResult {
  session_id: string;
  status: string;
  ws_url: string;
}

export async function runFlow(payload: FlowPayload): Promise<RunResult> {
  const response = await fetch(`${BASE}/api/agents/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  const data = (await response.json()) as { session_id: string; status: string };
  return {
    session_id: data.session_id,
    status: data.status,
    ws_url: `${process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000'}/ws/${data.session_id}`,
  };
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
