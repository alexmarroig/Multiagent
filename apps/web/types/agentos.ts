export type AgentCategory =
  | 'financial'
  | 'marketing'
  | 'phone'
  | 'excel'
  | 'travel'
  | 'supervisor'
  | 'utility';

export type NodeStatus = 'idle' | 'running' | 'done' | 'error';

export type RunState = 'idle' | 'running' | 'done' | 'error';

export type AgentNodeData = {
  label: string;
  category: AgentCategory;
  description: string;
  model: string;
  prompt: string;
  tools: string[];
  status?: NodeStatus;
};

export type AgentTemplate = {
  id: string;
  name: string;
  category: AgentCategory;
  description: string;
  defaultTools: string[];
  defaultPrompt: string;
};

export const AGENT_COLOR: Record<AgentCategory, string> = {
  financial: '#16a34a',
  marketing: '#2563eb',
  phone: '#7c3aed',
  excel: '#eab308',
  travel: '#f97316',
  supervisor: '#111827',
  utility: '#64748b',
};

export const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: 'financial-analyst',
    name: 'FinancialAnalystAgent',
    category: 'financial',
    description: 'Análise financeira, DRE, fluxo de caixa e geração de Excel.',
    defaultTools: ['yfinance', 'pandas', 'openpyxl'],
    defaultPrompt: 'Analise os dados financeiros e gere recomendações acionáveis.',
  },
  {
    id: 'travel-agent',
    name: 'TravelAgent',
    category: 'travel',
    description: 'Pesquisa voos/hotéis e sugere roteiro com otimização de custo.',
    defaultTools: ['playwright', 'tavily', 'calendar'],
    defaultPrompt: 'Planeje uma viagem completa com foco em custo-benefício.',
  },
  {
    id: 'meeting-agent',
    name: 'MeetingAgent',
    category: 'utility',
    description: 'Agenda reuniões e faz follow-up automático.',
    defaultTools: ['google-calendar', 'apscheduler', 'email-api'],
    defaultPrompt: 'Organize agenda, convites e lembretes automaticamente.',
  },
  {
    id: 'phone-agent',
    name: 'PhoneAgent',
    category: 'phone',
    description: 'Dispara ligações automatizadas via Twilio com script customizado.',
    defaultTools: ['twilio', 'tts', 'stt'],
    defaultPrompt: 'Realize ligações objetivas com roteiro profissional.',
  },
  {
    id: 'excel-agent',
    name: 'ExcelAgent',
    category: 'excel',
    description: 'Cria planilhas, dashboards e fórmulas automaticamente.',
    defaultTools: ['openpyxl', 'pandas'],
    defaultPrompt: 'Construa uma planilha executiva com gráficos e insights.',
  },
  {
    id: 'marketing-agent',
    name: 'MarketingAgent',
    category: 'marketing',
    description: 'Pesquisa mercado e gera campanhas com assets textuais.',
    defaultTools: ['tavily', 'email-api'],
    defaultPrompt: 'Crie uma campanha completa com abordagem de alto ROI.',
  },
  {
    id: 'supervisor-agent',
    name: 'SupervisorAgent',
    category: 'supervisor',
    description: 'Coordena os demais agentes e valida resultados.',
    defaultTools: ['langgraph', 'evaluation'],
    defaultPrompt: 'Orquestre o fluxo, valide qualidade e consolide saída final.',
  },
];
