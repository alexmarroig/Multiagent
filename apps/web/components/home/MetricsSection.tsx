import { MetricCard } from '@/components/home/MetricCard';

const metrics = [
  {
    title: 'Retorno anualizado',
    value: '18.42%',
    description: 'Leitura consolidada com múltiplas estratégias e proteção ativa.',
  },
  {
    title: 'Risco monitorado',
    value: '73/100',
    description: 'Cobertura quantitativa com alertas em tempo real por carteira.',
  },
  {
    title: 'Objetivos ativos',
    value: '12',
    description: 'Metas patrimoniais acompanhadas com contexto operacional contínuo.',
  },
  {
    title: 'Alertas críticos',
    value: '34',
    description: 'Sinais priorizados para resposta rápida da equipe de investimento.',
  },
];

export function MetricsSection() {
  return (
    <section className="py-12 md:py-16 border-t border-neutralDark-300">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric) => (
            <MetricCard key={metric.title} title={metric.title} value={metric.value} description={metric.description} />
          ))}
        </div>
      </div>
    </section>
  );
}
