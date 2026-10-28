import { Link, useParams } from 'react-router-dom';
import { ArrowRight, Check } from 'lucide-react';
import { care } from '../data/care';
import { moduleFeatures } from '../data/features';
import type { ModuleId } from '../data/features';
import { DashboardPreview, FAQ, FinalCTA, SectionHeading, WhyFamilyCare } from '../components/Sections';

function CareDetail({ id, pageHeading = false }: { id: ModuleId; pageHeading?: boolean }) {
  const service = care.find(item => item.id === id)!;
  const Heading = pageHeading ? 'h1' : 'h2';
  return <section id={id} className={`module-detail content-section ${service.theme}`}>
    <div className="module-introduction"><div className="module-photo"><img src={service.image} alt={service.alt} loading="lazy" /><span className="badge"><service.icon size={17} />{service.label}</span></div><div><span className="eyebrow">{id === 'child' ? 'A HEALTHY START' : id === 'women' ? 'YOUR HEALTH. YOUR CHOICE.' : 'EVERYDAY HEALTH, IN VIEW'}</span><Heading>{service.title}</Heading><h3>{service.description}</h3><p>{service.detail}</p><small className="preview-note">{id === 'child' ? 'Coverage: ages 0–12. Schedules require age, history and clinician review; no dose calculator is live.' : id === 'women' ? 'Enable only the trackers you need. Pregnancy and PCOS are optional; adolescent accounts need additional privacy and consent controls.' : 'Monitoring and record management — not automatic diagnosis or treatment prescription.'}</small></div></div>
    <div className="module-features">{moduleFeatures[id].map(([title, text]) => <article key={title}><Check size={18} /><div><h4>{title}</h4><p>{text}</p></div></article>)}</div>
    <div className="module-dashboard"><div><span className="eyebrow">A LOOK AT THE EXPERIENCE</span><h3>Your {service.title.toLowerCase()} dashboard, reimagined.</h3><p>Interactive concept with fictional data. Account features are planned, not connected to live patient records.</p></div><DashboardPreview key={id} initialModule={id} locked /></div>
  </section>;
}

export default function Services() {
  return <><section className="services-page-heading services-photo-hero"><div><span className="eyebrow">OUR SERVICES</span><h1>Complete Healthcare<br /><span>for Every Stage of Life.</span></h1><p>Child care, women’s health and adult wellness — health information organized around the people you love.</p></div><img src="/images/family.png" alt="Parents embracing their daughter" /></section><nav id="care-options" className="care-category-links" aria-label="Service categories">{care.map(service => <a key={service.id} className={service.theme} href={`#${service.id}`}><service.icon size={18} />{service.title}<ArrowRight size={16} /></a>)}</nav>{care.map(service => <CareDetail id={service.id as ModuleId} key={service.id} />)}<WhyFamilyCare /><FAQ /><FinalCTA /></>;
}

export function CareDetailsPage() {
  const { area } = useParams();
  const mapping: Record<string, ModuleId> = { 'child-care': 'child', 'womens-health': 'women', 'adult-health': 'adult' };
  const id = area ? mapping[area] : undefined;
  if (!id) return <section className="not-found"><h1>Care area not found</h1><Link to="/services" className="button primary">Explore our services</Link></section>;
  return <><div className="detail-breadcrumb"><Link to="/services">All services</Link><ArrowRight size={15} />{care.find(item => item.id === id)?.title}</div><CareDetail id={id} pageHeading /><SectionHeading eyebrow="MORE QUESTIONS?" title="Explore care with confidence." /><FAQ /><FinalCTA /></>;
}
