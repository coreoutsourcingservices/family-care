'use client';
import {useEffect,useRef,useState} from 'react';
import {Check,ExternalLink,LoaderCircle,RefreshCw,ShieldCheck,X} from 'lucide-react';
import {post} from '@/lib/api';
import type {User} from '@/lib/types';

type ReferenceCheck = {
 status:string; message?:string; limitation?:string; provider?:string; pincode?:string;
 comparisons?:{registration:boolean;name:boolean;council:boolean|null};
 records?:{name:string;registration:string;council:string}[];
 areas?:{state:string;district:string;post_office:string}[];
 locations?:{display_name:string;latitude:string;longitude:string}[];
};
export type VerificationReport = {
 checked_at:string; registration:ReferenceCheck; address:ReferenceCheck;
 clinic_postal:ReferenceCheck;clinic:ReferenceCheck;requires_admin_review:boolean;auto_approved:boolean;
};
export function DoctorDetails({person}:{person:User}) {
 const doctor=person.doctor;
 return <dl className="doctor-review-details">{[
  ['Full name',person.full_name],['Email',person.email],['Mobile number',person.phone_number],
  ['Qualification',doctor?.qualification],['Registration number',doctor?.medical_registration_number],
  ['Medical council',doctor?.registering_council],['Specialization',doctor?.specialization],['NMR ID',doctor?.nmr_id],
  ['Doctor address',doctor?.address],['Clinic address',doctor?.clinic_address],['Years of experience',doctor?.years_of_experience],
 ].map(([label,value])=><div key={String(label)}><dt>{label}</dt><dd>{value??'—'}</dd></div>)}</dl>;
}
function Result({title,result}:{title:string;result:ReferenceCheck}) {
 return <article className="doctor-check-result"><div className="title-row"><h3>{title}</h3><span className={`badge ${['match','area_match','locations_found'].includes(result.status)?'approved':'pending'}`}>{result.status.replaceAll('_',' ')}</span></div>
 <p>{result.message}</p>{result.limitation&&<p>{result.limitation}</p>}
 {result.comparisons&&<p>Name: {result.comparisons.name?'match':'needs review'} · Council: {result.comparisons.council===null?'not returned':result.comparisons.council?'match':'needs review'} · Registration: {result.comparisons.registration?'match':'needs review'}</p>}
 {!!result.records?.length&&<details><summary>Returned registry records</summary>{result.records.map((row,index)=><p key={index}>{row.name} · {row.registration} · {row.council||'Council not returned'}</p>)}</details>}
 {!!result.areas?.length&&<p>PIN {result.pincode}: {[...new Set(result.areas.map(row=>`${row.district}, ${row.state}`))].join(' / ')}</p>}
 {result.locations?.map((row,index)=><p key={index}>{row.display_name}<br/>Location: {row.latitude}, {row.longitude}</p>)}
 <small>{result.provider}</small></article>;
}
export default function DoctorReview({person,onClose,onDecision}:{person:User;onClose:()=>void;onDecision:(action:'approve'|'reject')=>void}) {
 const [report,setReport]=useState<VerificationReport|null>(person.doctor?.verification_check??null);
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');const attempted=useRef(false);
 async function check(){setBusy(true);setError('');try{const response=await post<{verification_check:VerificationReport}>(`admin/doctors/${person.public_id}/check`);setReport(response.verification_check);}catch(failure){setError((failure as Error).message);}finally{setBusy(false);}}
 useEffect(()=>{if(!attempted.current){attempted.current=true;void check();}},[]);
 useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==='Escape')onClose();};document.addEventListener('keydown',close);return()=>document.removeEventListener('keydown',close);},[onClose]);
 return <div className="modal-backdrop"><section className="modal doctor-review-modal" role="dialog" aria-modal="true" aria-labelledby="doctor-check-title"><button className="modal-close icon-button" onClick={onClose} aria-label="Close doctor check"><X size={19}/></button>
  <h2 id="doctor-check-title"><ShieldCheck size={23}/> Check Doctor</h2><p>{person.full_name} · {person.public_id} · <strong>pending</strong></p>
  <DoctorDetails person={person}/><p className="doctor-check-explanation">These reference checks do not approve the doctor. Review the name, registration, council and both addresses before making your decision. Clinic address is sent to the location provider; only the PIN from the personal address is sent for postal lookup.</p>
  {busy&&<p role="status"><LoaderCircle className="spin" size={16}/> Checking registry, PIN areas and clinic location…</p>}
  {error&&<div className="alert error" role="alert">{error}</div>}
  {report&&<div className="doctor-check-results"><p>Last checked: {new Date(report.checked_at).toLocaleString()}</p><Result title="Registration, name and council" result={report.registration}/><Result title="Doctor address: postal area" result={report.address}/><Result title="Clinic address: postal area" result={report.clinic_postal}/><Result title="Clinic location" result={report.clinic}/></div>}
  <div className="doctor-official-links"><a href="https://www.nmc.org.in/information-desk/indian-medical-register/" target="_blank" rel="noreferrer">NMC official register <ExternalLink size={13}/></a><a href="https://delhimedicalcouncil.org.in/home/regi_search.html" target="_blank" rel="noreferrer">Delhi Medical Council <ExternalLink size={13}/></a><a href="https://facility.abdm.gov.in/searchV2" target="_blank" rel="noreferrer">ABDM facility registry <ExternalLink size={13}/></a></div>
  <p className="doctor-check-attribution">Clinic location data: © OpenStreetMap contributors. <a href="https://operations.osmfoundation.org/policies/nominatim/" target="_blank" rel="noreferrer">Nominatim usage policy</a>. Address lookup does not certify clinic registration or address ownership.</p>
  <div className="modal-actions"><button className="secondary" disabled={busy} onClick={()=>void check()}><RefreshCw size={14}/>Check again</button><button className="action-button approve" disabled={busy} onClick={()=>onDecision('approve')}><Check size={14}/>Approve</button><button className="action-button" disabled={busy} onClick={()=>onDecision('reject')}><X size={14}/>Reject</button></div>
 </section></div>;
}
