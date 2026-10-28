import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, CalendarDays, Check, ClipboardList, Heart, LockKeyhole, Plus, ShieldCheck, Stethoscope, Users } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { ModuleId } from '../data/features';
import { questions } from '../data/features';

export function openAccount(role: 'Customer' | 'Doctor' = 'Customer') {
  window.dispatchEvent(new CustomEvent('familycare-account', { detail: role }));
}

export function SectionHeading({ eyebrow, title, text }: { eyebrow: string; title: string; text?: string }) {
  return <div className="section-title"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2>{text && <p>{text}</p>}</div>;
}

export function WhyFamilyCare() {
  const features: [LucideIcon, string, string][] = [
    [ClipboardList, 'Records, together', 'A planned home for reports, prescriptions and the health history you need.'],
    [Bell, 'Little things, remembered', 'Vaccination, appointment, screening and prescribed medicine reminders.'],
    [Users, 'One family, individual profiles', 'Separate health histories for the family members you are authorized to manage.'],
    [Stethoscope, 'Context for your doctor', 'Share the relevant history with a doctor when you choose to authorize access.'],
    [CalendarDays, 'Care across life stages', 'Child, women’s and adult health modules, organized around different needs.'],
    [LockKeyhole, 'Consent at the center', 'Profile permissions and doctor authorization are part of the planned access model.'],
  ];
  return <section className="content-section" id="why-familycare"><SectionHeading eyebrow="WHY FAMILYCARE+" title="Less scattered. More connected." text="A platform being built around the everyday work of looking after a family." /><div className="feature-grid">{features.map(([Icon, title, text], index) => <article className={`feature-tile tone-${index % 4}`} key={title}><span className="icon-circle"><Icon /></span><h3>{title}</h3><p>{text}</p></article>)}</div></section>;
}

export function HowItWorks({ doctorReview = false }: { doctorReview?: boolean }) {
  const steps = [
    ['Register', 'Create your own customer account. Doctor registration follows a separate verification flow.'],
    ['Select a module', 'Choose child care, women’s health or adult health for the relevant profile.'],
    ['Complete a profile', 'Add the person’s details with the appropriate permission or guardian authorization.'],
    ['Track health', 'Keep records and measurements organized over time. Review them with a qualified clinician.'],
    ...(doctorReview ? [['Doctor review', 'Authorize a doctor to review relevant records and discuss the next steps with you.']] : []),
  ];
  const [active, setActive] = useState(0);
  return <section className="content-section soft-section"><SectionHeading eyebrow="HOW IT WORKS" title="A little clarity, one step at a time." /><div className="steps-flow">{steps.map(([title], index) => <button aria-pressed={active === index} onClick={() => setActive(index)} className={active === index ? 'selected' : ''} key={title}><span>{String(index + 1).padStart(2, '0')}</span><strong>{title}</strong>{index < steps.length - 1 && <ArrowRight size={19} />}</button>)}</div><p className="step-explanation" aria-live="polite">{steps[active][1]}</p><small className="preview-note">Planned account journey · explore each step</small></section>;
}

export function DashboardPreview({ initialModule = 'child', locked = false }: { initialModule?: ModuleId; locked?: boolean }) {
  const [module, setModule] = useState<ModuleId>(initialModule);
  const [womenView, setWomenView] = useState('Cycle');
  const [adultView, setAdultView] = useState('Blood pressure');
  return <div className={`dashboard-preview ${module === 'child' ? 'blue' : module === 'women' ? 'pink' : 'teal'}`}>
    <div className="dashboard-top"><span><span className="status-dot" /> FamilyCare+ / {module === 'child' ? 'Child Care' : module === 'women' ? 'Women’s Health' : 'Adult Health'}</span><span className="demo-badge">DEMO DATA</span></div>
    {!locked && <div className="module-tabs" aria-label="Dashboard module">{([['child', 'Child Care'], ['women', 'Women’s Health'], ['adult', 'Adult Health']] as [ModuleId, string][]).map(([id, title]) => <button key={id} aria-pressed={module === id} onClick={() => setModule(id)}>{title}</button>)}</div>}
    <div className="dashboard-body">
      {module === 'child' ? <><div className="dashboard-heading"><div><small>CHILD HEALTH OVERVIEW</small><h3>Aarav’s little milestones</h3><p>Age 4 · Fictional child profile</p></div><span className="icon-circle"><Heart /></span></div><div className="mini-stats"><div><small>Health records</small><strong>12 <span>sample entries</span></strong></div><div><small>Next activity</small><strong>Follow-up <span>demo reminder</span></strong></div><div><small>Milestones</small><strong>8 <span>logged in preview</span></strong></div></div><h4>Vaccination record timeline</h4><div className="vaccine-timeline"><div><span><Check size={16} /></span><strong>Recorded dose</strong><small>Doctor-verified · sample</small></div><div><span><ClipboardList size={16} /></span><strong>Added by guardian</strong><small>Self-reported · not verified</small></div><div><span><CalendarDays size={16} /></span><strong>Upcoming review</strong><small>Schedule to be set by clinician</small></div></div><p className="dashboard-footnote">Illustrative records only. No vaccine dates or doses are calculated in this preview.</p></> : module === 'women' ? <><div className="dashboard-heading"><div><small>YOUR HEALTH, YOUR CHOICES</small><h3>Choose the tracker that fits you.</h3><p>Fictional profile · optional trackers</p></div><span className="icon-circle"><Heart /></span></div><div className="module-tabs sub-tabs">{['Cycle', 'Pregnancy', 'PCOS'].map(view => <button aria-pressed={womenView === view} onClick={() => setWomenView(view)} key={view}>{view}</button>)}</div>{womenView === 'Cycle' ? <><div className="calendar-caption"><strong>Sample cycle calendar</strong><span>Logged days <i /></span></div><div className="cycle-calendar">{['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => <small key={i}>{day}</small>)}{Array.from({ length: 28 }, (_, i) => <span className={i >= 7 && i <= 11 ? 'logged' : ''} key={i}>{i + 1}</span>)}</div><p className="dashboard-footnote">Example history, not a fertility prediction or medical recommendation.</p></> : <div className="tracker-example"><span className="icon-circle"><ClipboardList /></span><h4>{womenView === 'Pregnancy' ? 'A place for each new chapter.' : 'Your history, easier to review.'}</h4><p>{womenView === 'Pregnancy' ? 'Organize trimester notes, scans and a doctor-approved checkup plan.' : 'Keep diagnosis history, tests and prescribed medicines together.'}</p><span className="demo-badge">OPTIONAL TRACKER · PREVIEW</span></div>}</> : <><div className="dashboard-heading"><div><small>ADULT HEALTH OVERVIEW</small><h3>Small readings. A clearer history.</h3><p>Fictional profile · sample measurements</p></div><span className="icon-circle"><Heart /></span></div><div className="module-tabs sub-tabs">{['Blood pressure', 'Glucose'].map(view => <button aria-pressed={adultView === view} key={view} onClick={() => setAdultView(view)}>{view}</button>)}</div><div className="chart-caption"><strong>{adultView === 'Blood pressure' ? 'Blood pressure history' : 'Glucose history'}</strong><span>{adultView === 'Blood pressure' ? 'mmHg · systolic / diastolic' : 'mg/dL · example readings'}</span></div><svg className="health-chart" viewBox="0 0 600 170" role="img" aria-label={adultView === 'Blood pressure' ? 'Sample blood pressure readings across six entries; systolic 128, 124, 130, 122, 126, 120; diastolic 84, 80, 82, 78, 80, 78 millimeters of mercury.' : 'Sample glucose readings across six entries: 116, 120, 108, 112, 104, 110 milligrams per deciliter.'}><g stroke="#dcece9" strokeDasharray="4 5">{[25, 60, 95, 130].map(y => <line key={y} x1="35" x2="575" y1={y} y2={y} />)}</g><polyline points={adultView === 'Blood pressure' ? '40,55 145,69 250,48 355,76 460,62 565,83' : '40,65 145,51 250,93 355,79 460,107 565,86'} fill="none" stroke="#008e91" strokeWidth="4" strokeLinejoin="round" />{adultView === 'Blood pressure' && <polyline points="40,117 145,127 250,122 355,132 460,127 565,132" fill="none" stroke="#8b79ef" strokeWidth="3" />}{[40, 145, 250, 355, 460, 565].map((x, i) => <text key={x} x={x} y="161" textAnchor="middle" fill="#657b91" fontSize="11">Entry {i + 1}</text>)}</svg><p className="dashboard-footnote">Demonstration values only. Trends do not provide a diagnosis or treatment advice.</p></>}
    </div>
  </div>;
}

export function PlatformPreview() {
  return <section className="content-section"><SectionHeading eyebrow="TAKE A LOOK INSIDE" title="A clearer picture of everyday health." text="Switch between the interactive dashboard concepts. All profiles and readings below are fictional." /><DashboardPreview /></section>;
}

export function FamilyProfiles() {
  const profiles = [{ name: 'Aarav', role: 'Child · guardian-managed', initial: 'A', theme: 'blue', info: 'Vaccination records, growth notes and developmental milestones.', permission: 'Guardian permission required' }, { name: 'Meera', role: 'Adult · personal profile', initial: 'M', theme: 'pink', info: 'Selected women’s health trackers, reports and care history.', permission: 'Managed by the profile owner' }, { name: 'Raj', role: 'Adult · shared with consent', initial: 'R', theme: 'teal', info: 'Blood pressure history, lab reports and prescribed medicine records.', permission: 'Explicit adult authorization required' }];
  const [active, setActive] = useState(0);
  return <section className="content-section soft-section family-section"><div><span className="eyebrow">ONE ACCOUNT. YOUR FAMILY.</span><h2>Individual stories.<br />Connected care.</h2><p>Manage separate profiles for the family members you are authorized to support. Each person keeps their own health history.</p><small className="preview-note">Fictional profiles · selection changes this preview only</small></div><div className="family-profile-panel"><div className="profile-options">{profiles.map((profile, index) => <button className={profile.theme} aria-pressed={active === index} onClick={() => setActive(index)} key={profile.name}><span>{profile.initial}</span><strong>{profile.name}</strong></button>)}</div><div className="profile-detail" aria-live="polite"><span className="demo-badge">PROFILE PREVIEW</span><h3>{profiles[active].name}</h3><small>{profiles[active].role}</small><p>{profiles[active].info}</p><span className="permission-note"><ShieldCheck size={16} />{profiles[active].permission}</span></div></div></section>;
}

export function DoctorSection() {
  return <section id="doctor-consultation" className="content-section doctor-section"><div className="doctor-visual"><span className="doctor-symbol"><Stethoscope size={72} /></span><div className="doctor-visual-card"><ShieldCheck /><div><strong>Built around responsible access</strong><small>Registration → verification → authorized review</small></div></div><span className="demo-badge">PLANNED DOCTOR EXPERIENCE</span></div><div><span className="eyebrow">FOR THE PEOPLE WHO CARE</span><h2>Give every consultation<br />a little more context.</h2><p>A dedicated doctor journey is planned for registration, professional verification, appointment management and consent-based access to relevant patient records.</p><ul className="check-list"><li><Check />Separate doctor registration</li><li><Check />Registration-number verification before access</li><li><Check />Patient-authorized record review</li></ul><button className="button primary" onClick={() => openAccount('Doctor')}>Register as a Doctor <ArrowRight size={17} /></button><small className="preview-note">Registration and verification are not live yet.</small></div></section>;
}

export function ReminderPreview() {
  const [enabled, setEnabled] = useState([true, true, false, true]);
  return <section className="content-section soft-section reminder-section"><div><span className="eyebrow">A LITTLE HELP REMEMBERING</span><h2>Make room for life.<br />Keep care in view.</h2><p>Planned reminders bring upcoming care into one place. Explore the notification preview without sending or scheduling anything.</p><small className="preview-note">Demo switches only · no real notifications</small></div><div className="reminder-panel">{[['Vaccination review', 'Review the next steps with your child’s doctor.'], ['Prescribed medicine', 'Based on the schedule provided by your clinician.'], ['Upcoming appointment', 'A little reminder before a planned doctor visit.'], ['Preventive screening', 'Keep your clinician-approved screening plan in view.']].map(([title, text], index) => <div className="reminder-row" key={title}><span className="icon-circle"><Bell /></span><div><strong>{title}</strong><small>{text}</small></div><button className="switch" role="switch" aria-label={`${title} preview`} aria-checked={enabled[index]} onClick={() => setEnabled(previous => previous.map((value, i) => i === index ? !value : value))}><span /></button></div>)}</div></section>;
}

export function FAQ() {
  return <section className="content-section faq-section" id="faq"><SectionHeading eyebrow="A FEW THINGS YOU MIGHT WONDER" title="Your questions, answered." /><div className="faq-list">{questions.map(([question, answer]) => <details key={question}><summary>{question}<Plus size={18} /></summary><p>{answer}</p></details>)}</div></section>;
}

export function FinalCTA() {
  return <section className="final-cta"><span className="eyebrow">FOR TODAY. FOR TOMORROW. FOR YOUR FAMILY.</span><h2>Start Your Family’s<br />Health Journey.</h2><p>One place for every generation. A little more clarity for the care ahead.</p><div><button className="button cta-white" onClick={() => openAccount()}>Join FamilyCare+ <ArrowRight size={18} /></button><button className="button cta-outline" onClick={() => openAccount('Doctor')}>Register as Doctor</button></div><small>Explore the concept today. Account access is coming next.</small></section>;
}

export function CareAreaLinks() {
  return <div className="care-area-links">{[['child', 'Child Care', '0–12 years', 'blue'], ['women', 'Women’s Health', 'Your choice of trackers', 'pink'], ['adult', 'Adult Health', '18+ years', 'teal']].map(([id, title, subtitle, theme]) => <Link to={`/services#${id}`} className={theme} key={id}><Heart /><h3>{title}</h3><p>{subtitle}</p><span>Explore care <ArrowRight size={17} /></span></Link>)}</div>;
}
