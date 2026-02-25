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
    description: 'Especialista em análise de demonstrativos, fluxo de caixa, projeções DRE e geração de relatórios executivos em Excel.',
    defaultTools: ['finance', 'excel', 'search'],
    defaultPrompt: 'Você é um Analista Financeiro Sênior. Sua missão é processar dados brutos, identificar tendências de mercado e consolidar um relatório estratégico com indicadores-chave (KPIs) e recomendações de otimização de custos.',
  },
  {
    id: 'travel-agent',
    name: 'TravelAgent',
    category: 'travel',
    description: 'Orquestrador de logística global. Pesquisa voos, hospedagem e transportes com foco em eficiência de tempo e custo-benefício.',
    defaultTools: ['browser', 'search', 'calendar', 'travel'],
    defaultPrompt: 'Você é um Consultor de Viagens Corporativas. Sua tarefa é criar um itinerário completo e otimizado, considerando restrições de orçamento, preferências de conforto e integração com calendários de reuniões.',
  },
  {
    id: 'meeting-agent',
    name: 'MeetingAgent',
    category: 'utility',
    description: 'Gestor de agenda e comunicações. Automatiza agendamentos, envia convites e realiza follow-ups inteligentes pós-reunião.',
    defaultTools: ['calendar', 'browser'],
    defaultPrompt: 'Atue como um Assistente Executivo de Alta Performance. Coordene horários entre múltiplos participantes, verifique disponibilidade em tempo real e garanta que todos os requisitos da reunião (sala, link, pauta) estejam prontos.',
  },
  {
    id: 'phone-agent',
    name: 'PhoneAgent',
    category: 'phone',
    description: 'Interface de voz automatizada. Realiza chamadas via VoIP, coleta dados de entrada e executa scripts de atendimento humanizado.',
    defaultTools: ['phone', 'search'],
    defaultPrompt: 'Você é um Agente de Voz especializado em triagem e atendimento. Execute o roteiro de ligação com clareza, colete as informações necessárias do interlocutor e registre o log detalhado da interação para o sistema central.',
  },
  {
    id: 'excel-agent',
    name: 'ExcelAgent',
    category: 'excel',
    description: 'Analista de dados tabular. Cria dashboards dinâmicos, automatiza fórmulas complexas e limpa grandes volumes de dados.',
    defaultTools: ['excel', 'utility'],
    defaultPrompt: 'Transforme dados brutos em inteligência visual. Sua função é criar estruturas de planilhas eficientes, aplicar macros/fórmulas avançadas e gerar sumários executivos que facilitem a tomada de decisão.',
  },
  {
    id: 'marketing-agent',
    name: 'MarketingAgent',
    category: 'marketing',
    description: 'Estrategista de growth e conteúdo. Analisa concorrência, gera copy persuasivo e planeja campanhas multicanal de alto impacto.',
    defaultTools: ['search', 'browser'],
    defaultPrompt: 'Você é um CMO Digital. Pesquise tendências atuais do nicho solicitado, analise a concorrência e desenvolva um plano de marketing completo, incluindo sugestões de anúncios, palavras-chave e funis de conversão.',
  },
  {
    id: 'supervisor-agent',
    name: 'SupervisorAgent',
    category: 'supervisor',
    description: 'Núcleo de inteligência central. Supervisiona a execução dos agentes, resolve conflitos de lógica e valida a entrega final.',
    defaultTools: ['search', 'utility'],
    defaultPrompt: 'Você é o Coordenador Central do Fluxo. Sua responsabilidade é delegar subtarefas para os agentes especializados, revisar a qualidade de cada saída e sintetizar um resultado final coeso que atenda plenamente ao objetivo do usuário.',
  },
];
