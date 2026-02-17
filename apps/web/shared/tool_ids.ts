export const TOOL_IDS = ['finance', 'excel', 'phone', 'calendar', 'search', 'browser', 'travel'] as const;

export type ToolId = (typeof TOOL_IDS)[number];

const TOOL_ID_SET = new Set<string>(TOOL_IDS);

export const TOOL_ID_ALIASES: Record<string, ToolId> = {
  yfinance: 'finance',
  openpyxl: 'excel',
  pandas: 'excel',
  twilio: 'phone',
  'google-calendar': 'calendar',
  tavily: 'search',
  playwright: 'browser',
};

export function normalizeToolId(tool: string): ToolId | null {
  const normalized = tool.trim().toLowerCase();
  if (!normalized) return null;
  if (TOOL_ID_SET.has(normalized)) return normalized as ToolId;
  return TOOL_ID_ALIASES[normalized] ?? null;
}

export function normalizeToolIds(tools: string[]): { normalized: ToolId[]; unmapped: string[] } {
  const normalized: ToolId[] = [];
  const unmapped: string[] = [];

  for (const tool of tools) {
    const mapped = normalizeToolId(tool);
    if (mapped) {
      if (!normalized.includes(mapped)) normalized.push(mapped);
    } else {
      unmapped.push(tool);
    }
  }

  return { normalized, unmapped };
}
