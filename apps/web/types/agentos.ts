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
  financial: '#00f3ff', // Cyan
  marketing: '#ff00ff', // Magenta
  phone: '#0066ff',    // Blue
  excel: '#f3ff00',    // Yellow
  travel: '#ff8000',   // Orange
  supervisor: '#ffffff', // White
  utility: '#94a3b8',   // Slate
};

export const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: 'financial-analyst',
    name: 'FinancialAnalystAgent',
    category: 'financial',
    description: 'Expert em análise de mercado, forecasting (ARIMA/Prophet) e relatórios executivos avançados.',
    defaultTools: ['finance_api', 'excel_v2', 'search', 'plotting'],
    defaultPrompt: 'Você é um Analista Financeiro Sênior com expertise em Quantitative Finance. Sua missão inclui: 1. Integração com APIs de mercado (Yahoo Finance, B3) para dados em tempo real. 2. Realização de análises preditivas e forecasting usando modelos como ARIMA ou Prophet para fluxo de caixa e DRE. 3. Categorização automática de despesas e geração de insights estratégicos. 4. Exportação de dashboards interativos para Excel ou PDF.',
  },
  {
    id: 'travel-agent',
    name: 'TravelAgent',
    category: 'travel',
    description: 'Orquestrador de logística global com integração multimodal e otimização de custo-benefício.',
    defaultTools: ['skyscanner_api', 'booking_api', 'google_calendar', 'search'],
    defaultPrompt: 'Você é um Consultor de Viagens Corporativas de Elite. Suas responsabilidades são: 1. Pesquisa multimodal (voos, hotéis, transportes) usando APIs como Skyscanner e Booking. 2. Geração de itinerários detalhados integrados ao Google Calendar. 3. Otimização algorítmica de custo-benefício. 4. Monitoramento proativo de alterações e alertas climáticos.',
  },
  {
    id: 'meeting-agent',
    name: 'MeetingAgent',
    category: 'utility',
    description: 'Gestor de agenda inteligente com transcrição, sumarização e tradução em tempo real.',
    defaultTools: ['google_calendar_api', 'outlook_api', 'asr_whisper', 'translation'],
    defaultPrompt: 'Atue como um Assistente Executivo de Alta Performance. Suas funções incluem: 1. Sincronização inteligente entre Google Calendar e Outlook. 2. Uso de ASR (como Whisper) para transcrição e sumarização de reuniões em itens de ação. 3. Tradução simultânea entre idiomas. 4. Gravação e indexação de replays pesquisáveis.',
  },
  {
    id: 'phone-agent',
    name: 'PhoneAgent',
    category: 'phone',
    description: 'Voicebot inteligente com reconhecimento de intenção e integração nativa com CRM.',
    defaultTools: ['twilio_voip', 'nlu_intent', 'hubspot_crm', 'salesforce_crm'],
    defaultPrompt: 'Você é um Agente de Voz especializado em NLU (Natural Language Understanding). Suas tarefas: 1. Atuar como um voicebot inteligente que detecta intenções complexas do interlocutor. 2. Registro detalhado de chamadas com áudio e transcrição. 3. Integração bidirecional com CRM (Salesforce/HubSpot) para histórico de atendimento em tempo real.',
  },
  {
    id: 'excel-agent',
    name: 'ExcelAgent',
    category: 'excel',
    description: 'Analista de dados tabular com automação via Python (pandas) e conexão direta a DBs.',
    defaultTools: ['python_pandas', 'matplotlib', 'postgresql_connector', 'excel_macros'],
    defaultPrompt: 'Transforme dados brutos em inteligência visual e estruturada. Suas capacidades incluem: 1. Automação avançada usando scripts Python (pandas/matplotlib) integrados. 2. Validação rigorosa de dados e detecção de anomalias. 3. Conexão direta com bancos de dados (PostgreSQL/MySQL) para extração e carga de dados. 4. Geração de tabelas dinâmicas e macros complexas.',
  },
  {
    id: 'marketing-agent',
    name: 'MarketingAgent',
    category: 'marketing',
    description: 'Estrategista de growth multicanal com análise competitiva e automação de copy.',
    defaultTools: ['semrush_api', 'openai_copy', 'ad_manager', 'search'],
    defaultPrompt: 'Você é um CMO Digital focado em ROI. Suas missões: 1. Análise competitiva profunda usando ferramentas de SEO/SEM. 2. Geração de copy persuasivo otimizado para conversão. 3. Planejamento e automação de campanhas multicanal. 4. Dashboards de performance e métricas de funil.',
  },
  {
    id: 'supervisor-agent',
    name: 'SupervisorAgent',
    category: 'supervisor',
    description: 'Núcleo de orquestração avançada com roteamento condicional e persistência de estado.',
    defaultTools: ['langgraph_core', 'state_checkpoint', 'observability_trace'],
    defaultPrompt: 'Você é o Coordenador Central de Orquestração. Sua inteligência permite: 1. Controle de fluxo avançado com roteamento condicional (if/else) e execução paralela. 2. Persistência de estado via checkpoints para retomada de missões interrompidas. 3. Observabilidade total via traces de execução e contagem de tokens. 4. Implementação de políticas de fallback e retry automático.',
  },
];
