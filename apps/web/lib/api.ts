const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function getAuthHeader() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('agentos_token') : null;
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

export type Template = {
  id: string;
  name: string;
  description: string;
  agents: string[];
  color: 'orange' | 'blue' | 'green' | 'purple';
  inputs: string[];
};

export async function runFlow(payload: FlowPayload): Promise<RunResult> {
  const r = await fetch(`${BASE}/api/agents/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });

  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);

  const data = (await r.json()) as { session_id: string; status: string };
  return {
    session_id: data.session_id,
    status: data.status,
    ws_url: `${process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000'}/ws/${data.session_id}`,
  };
}

export async function fetchTemplates(): Promise<{ templates: Template[] }> {
  const r = await fetch(`${BASE}/api/agents/templates`);
  const raw = (await r.json()) as Template[] | { templates: Template[] };
  const templates = Array.isArray(raw) ? raw : raw.templates;
  return { templates };
}

export async function downloadExcel(config: {
  title: string;
  data: Record<string, unknown>[];
  filename?: string;
}) {
  const r = await fetch(`${BASE}/api/tools/excel/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(config),
  });

  if (!r.ok) throw new Error('Falha ao gerar Excel');

  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = config.filename ?? 'relatorio.xlsx';
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadArtifactExcel(config: { artifact_id?: string; artifact_path?: string }) {
  const params = new URLSearchParams();
  if (config.artifact_id) params.set('artifact_id', config.artifact_id);
  if (config.artifact_path) params.set('artifact_path', config.artifact_path);

  const r = await fetch(`${BASE}/api/tools/artifacts/download?${params.toString()}`, {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!r.ok) throw new Error('Falha ao baixar artefato Excel');

  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;

  const filenameFromHeader = r.headers.get('content-disposition')?.match(/filename="?([^";]+)"?/)?.[1];

  a.download = filenameFromHeader ?? config.artifact_id ?? 'relatorio.xlsx';
  a.click();
  URL.revokeObjectURL(url);
}

export async function scheduleMeeting(config: {
  title: string;
  start_datetime: string;
  end_datetime: string;
  description?: string;
  attendees?: string[];
}) {
  const r = await fetch(`${BASE}/api/tools/calendar/schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(config),
  });
  return r.json();
}

export async function makeCall(config: {
  to_number: string;
  script: string;
  language?: string;
}) {
  const r = await fetch(`${BASE}/api/tools/phone/call`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(config),
  });
  return r.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`);
    return r.ok;
  } catch {
    return false;
  }
}
