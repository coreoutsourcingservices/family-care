import {useEffect, useState} from 'react';
import {RefreshCw, ShieldCheck} from 'lucide-react';
import {careApi} from '../../../../app/src/lib/careApi';
import type {ChildEntry} from './childRecords';

type Reminder={message?:string;source?:string;id:string;kind:string;title:string;date:string;status:string;delivery_status:string};
type Summary={child:{age:{display:string;primary_category:string}};counts:Record<string,number>;vaccination:{message:string;status:string}};
type Guide={status:string;message:string};
type Reminders={items:Reminder[];preferences:{in_app:boolean};message:string};
export function useChildSummary(profileId:string,entries:ChildEntry[]){
 const [data,setData]=useState<{dashboard:Summary;age:{display:string};guide:Guide;reminders:Reminders}>();
 const [error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 useEffect(()=>{let active=true;setError('');const base='/children/'+profileId;Promise.all([
  careApi<Summary>(base+'/dashboard'),careApi<{age:{display:string}}>(base+'/age'),careApi<Guide>(base+'/health-guide'),careApi<Reminders>(base+'/reminders'),
 ]).then(([dashboard,age,guide,reminders])=>{if(active)setData({dashboard,age:age.age,guide,reminders});}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[profileId,entries,attempt]);
 useEffect(()=>{let active=true;let running=false;async function refresh(){if(document.hidden||running)return;running=true;try{const reminders=await careApi<Reminders>('/children/'+profileId+'/reminders');if(active)setData(previous=>previous?{...previous,reminders}:previous);}catch{/* Keep existing reminders until a successful refresh. */}finally{running=false;}}const timer=window.setInterval(refresh,60000);window.addEventListener('focus',refresh);document.addEventListener('visibilitychange',refresh);return()=>{active=false;clearInterval(timer);window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',refresh);};},[profileId]);
 return {data,error,reload:()=>setAttempt(v=>v+1)};
}
export function ChildHealthSummary({data,error,onRetry}: {data:ReturnType<typeof useChildSummary>['data'];error:string;onRetry:()=>void}){
 return <section className="ch-panel ch-connected-panel"><div className="ch-section-top"><div><span className="ch-eyebrow">YOUR ACCOUNT, CONNECTED</span><h2>Child health overview</h2></div><ShieldCheck/></div>{error?<p role="alert" className="ch-error">{error} <button className="ch-button secondary" onClick={onRetry}><RefreshCw size={15}/>Try again</button></p>:data?<>
  <div className="ch-mini-stats"><article><span>Age today<strong>{data.age.display}</strong></span></article><article><span>Recorded vaccinations<strong>{data.dashboard.counts.vaccination??0}</strong></span></article><article><span>In-app reminders<strong>{data.reminders.items.length}</strong></span></article></div>
  <div className="ch-clinical-status"><strong>{data.dashboard.vaccination.status==='AVAILABLE'?'Published vaccination schedule':'Vaccination schedule - not published'}</strong><p>{data.dashboard.vaccination.message}</p></div><div className="ch-clinical-status"><strong>Health guidance — not published</strong><p>{data.guide.message}</p></div>
 </>:<p role="status">Loading child health overview...</p>}</section>;
}
export function ReminderPreferences({profileId,data,onRefresh}:{profileId:string;data:Reminders|undefined;onRefresh:()=>void}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 async function update(){if(!data)return;setBusy(true);setError('');try{await careApi('/children/'+profileId+'/reminder-preferences',{in_app:!data.preferences.in_app},true,'PUT');onRefresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <section className="ch-panel"><h2>Reminder preferences</h2><p className="ch-muted">Show in-app reminders for recorded dates and eligible published schedules. Email reminders require opt-in on the Vaccination page and an enabled published reminder policy.</p>{data?<><button className="ch-button secondary" disabled={busy} aria-pressed={data.preferences.in_app} onClick={update}>{busy?'Saving...':data.preferences.in_app?'In-app reminders: on':'In-app reminders: off'}</button><div className="ch-record-list">{data.items.map(item=><article className="ch-record" key={item.id}><div><strong>{item.title}</strong><p>{item.date} · {item.message||(item.status==='OVERDUE'?'Past recorded date':'Upcoming recorded date')}</p><small>{item.source==='PUBLISHED_SCHEDULE'?'Published schedule reminder':'Parent-provided date'}</small></div></article>)}</div></>:<p role="status">Loading reminder preferences...</p>}{error&&<p role="alert" className="ch-error">{error}</p>}</section>;
}
