import type { LucideIcon } from 'lucide-react';

type Summary = { title: string; value: string; description: string; Icon: LucideIcon };
export default function HealthOverview({ title, age, summaries }: { title: string; age: string; summaries: Summary[] }) {
  return <>
    <div className="customer-overview-heading"><h2>{title}</h2><span>{age}</span></div>
    <div className="customer-summary-grid">{summaries.map(({ title: label, value, description, Icon }, index) =>
      <article className={`customer-summary-card tone-${index}`} key={label}>
        <span className="customer-summary-icon"><Icon size={24} /></span>
        <div><p>{label}</p><h3>{value}</h3><small>{description}</small></div>
      </article>)}
    </div>
  </>;
}
