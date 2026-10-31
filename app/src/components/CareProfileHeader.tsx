import {useEffect,useRef} from 'react';
import {gsap} from 'gsap';
import {Stethoscope,FileText,Syringe,Heart,CalendarDays} from 'lucide-react';
import type {TimelineEntry} from './CareTimeline';
import './care-profile-header.css';
export default function CareProfileHeader({name,dob,entries}:{name:string;dob:string;entries:TimelineEntry[]}){
 const root=useRef<HTMLElement>(null);
 useEffect(()=>{if(!root.current||matchMedia('(prefers-reduced-motion: reduce)').matches)return;const context=gsap.context(()=>{gsap.fromTo('.care-profile-identity,.care-profile-counter',{y:12,opacity:0},{y:0,opacity:1,duration:.4,stagger:.05,ease:'power2.out',clearProps:'transform,opacity'});},root);return()=>context.revert();},[name,dob]);
 const birth=new Date(dob+'T00:00:00'),today=new Date();let years=today.getFullYear()-birth.getFullYear(),months=today.getMonth()-birth.getMonth();if(today.getDate()<birth.getDate())months--;if(months<0){years--;months+=12;}const age=Number.isNaN(years)?'Age not recorded':`${years} years${months?', '+months+' months':''}`;
 const stats=[{label:'Consultations',icon:Stethoscope,tone:'blue',count:entries.filter(r=>['consultation','consultation_request'].includes(r.kind)).length},{label:'Prescriptions',icon:FileText,tone:'pink',count:entries.filter(r=>r.category==='Prescription').length},{label:'Vaccinations',icon:Syringe,tone:'mint',count:entries.filter(r=>r.kind==='vaccination').length},{label:'Care notes',icon:Heart,tone:'amber',count:entries.filter(r=>r.kind==='care'&&r.category!=='Prescription').length}];
 return <section className="care-profile-banner" ref={root} aria-label="Child care profile"><div className="care-profile-identity"><span className="care-profile-monogram">{name.split(' ').slice(0,2).map(n=>n[0]).join('')}</span><div><small>YOUR CHILD'S CARE SPACE</small><h2>{name}</h2><p>{age}</p><span><CalendarDays size={12}/>DOB: {dob?birth.toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):'Not recorded'}</span></div></div><div className="care-profile-counters">{stats.map(item=><article key={item.label} className={'care-profile-counter '+item.tone}><span><item.icon size={22}/></span><strong>{item.count}</strong><small>{item.label}</small></article>)}</div></section>;
}
