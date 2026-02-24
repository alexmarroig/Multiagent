const metricCards = [
  { title: 'Receita operacional', value: 'R$ 48,2M', description: 'Acumulado no trimestre com atualização diária.' },
  { title: 'Margem institucional', value: '27,4%', description: 'Eficiência consolidada entre unidades estratégicas.' },
  { title: 'Risco monitorado', value: '71/100', description: 'Cobertura de compliance e exposição em tempo real.' },
];

const activity = [
  'Motor de risco atualizou 128 eventos críticos.',
  '4 alçadas de aprovação concluídas nas últimas 2 horas.',
  'Sincronização com provedores externos está estável.',
  'Projeção de caixa recalculada para cenário defensivo.',
];

export default function DashboardPage() {
  return (
    <div className="space-y-6 pb-2">
      <section className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-lg transition-all duration-300 hover:border-neutral-700">
        <p className="text-sm font-medium text-neutral-400">Painel institucional</p>
        <h1 className="mt-2 max-w-4xl text-4xl font-semibold tracking-tight leading-tight text-pretty">
          Visão consolidada da operação enterprise
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-neutral-400 text-pretty">
          Monitoramento estratégico de receita, risco e performance em um cockpit compacto para times executivos.
        </p>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {metricCards.map((card) => (
          <article
            key={card.title}
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-lg transition-all duration-300 hover:border-neutral-700"
          >
            <h2 className="text-lg font-medium leading-snug text-neutral-300 text-balance">{card.title}</h2>
            <p className="mt-4 text-3xl font-bold tracking-tight">{card.value}</p>
            <p className="mt-2 text-sm leading-6 text-neutral-400 text-pretty">{card.description}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        <article className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-lg transition-all duration-300 hover:border-neutral-700 md:col-span-2">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2 className="text-lg font-medium text-neutral-300">Performance financeira</h2>
              <p className="mt-1 text-sm leading-6 text-neutral-400 text-pretty">Evolução semanal com base no consolidado multiunidade.</p>
            </div>
            <span className="whitespace-nowrap rounded-md border border-neutral-800 bg-neutral-950 px-2.5 py-1 text-xs font-medium text-neutral-400">
              Últimos 90 dias
            </span>
          </div>

          <div className="relative max-h-[320px] overflow-hidden rounded-xl border border-neutral-800 bg-[linear-gradient(to_right,rgba(64,64,64,0.18)_1px,transparent_1px),linear-gradient(to_bottom,rgba(64,64,64,0.18)_1px,transparent_1px)] bg-[size:30px_30px] p-4">
            <svg viewBox="0 0 700 260" className="h-[300px] w-full" fill="none" aria-label="Gráfico de performance">
              <path d="M30 210 L670 210" stroke="#404040" strokeWidth="1" />
              <path
                d="M30 170 C100 155, 130 120, 180 130 C230 140, 260 102, 320 110 C380 118, 430 78, 500 90 C560 102, 620 70, 670 82"
                stroke="#60A5FA"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M30 185 C100 176, 130 162, 180 158 C230 154, 260 140, 320 145 C380 150, 430 124, 500 130 C560 136, 620 118, 670 122"
                stroke="#93C5FD"
                strokeWidth="1.5"
                strokeLinecap="round"
                opacity="0.85"
              />
            </svg>
          </div>
        </article>

        <article className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-lg transition-all duration-300 hover:border-neutral-700">
          <h2 className="text-lg font-medium text-neutral-300">Eventos e alertas</h2>
          <ul className="mt-4 space-y-3">
            {activity.map((item) => (
              <li key={item} className="rounded-lg border border-neutral-800 bg-neutral-950 p-3 text-sm leading-6 text-neutral-400 text-pretty">
                {item}
              </li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
