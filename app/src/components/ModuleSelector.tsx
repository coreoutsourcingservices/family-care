import { ArrowRight, Baby, Heart, UserRound } from 'lucide-react';

export type ModuleId = 'child' | 'women' | 'adult';
const modules = [
  { id: 'child', title: 'Child Care', subtitle: '0-12 Years', Icon: Baby },
  { id: 'women', title: "Women's Health", subtitle: 'Personal health, reports & overall wellness.', Icon: Heart },
  { id: 'adult', title: 'Adult Health', subtitle: 'Everyday health, records & healthy living.', Icon: UserRound },
] as const;

export default function ModuleSelector({ selected, onSelect, translate = text => text }: { selected: ModuleId | null; onSelect: (id: ModuleId) => void; translate?: (text:string)=>string }) {
  return <div className="customer-module-selector" aria-label="Health sections">
    {modules.map(({ id, title, subtitle, Icon }) => <button key={id} type="button"
      className={`customer-module-card ${id}`} aria-pressed={selected === id}
      aria-controls="customer-module-content" onClick={() => onSelect(id)}>
      <img className="customer-module-photo" src={`/images/${id === 'women' ? 'women' : id}.png`} alt="" /><span className="customer-module-icon"><Icon size={20} strokeWidth={1.8} /></span>
      <span><strong>{translate(title)}</strong><small>{translate(subtitle)}</small></span>
      <span className="customer-card-arrow" aria-hidden="true"><ArrowRight size={15} /></span>
    </button>)}
  </div>;
}
