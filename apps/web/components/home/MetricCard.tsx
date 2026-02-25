type MetricCardProps = {
  title: string;
  value: string;
  description: string;
};

export function MetricCard({ title, value, description }: MetricCardProps) {
  return (
    <article className="rounded-xl border border-neutralDark-300 bg-neutralDark-200 p-6 shadow-md transition-all duration-300 ease-out hover:scale-105 hover:border-primary">
      <h3 className="text-sm font-medium text-neutral-300">{title}</h3>
      <h2 className="mt-2 text-3xl font-bold text-white">{value}</h2>
      <p className="mt-3 text-sm text-neutral-400">{description}</p>
    </article>
  );
}
