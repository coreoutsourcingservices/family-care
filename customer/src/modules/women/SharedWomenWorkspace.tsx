import {useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {careApi} from '../../../../app/src/lib/careApi';
import {downloadReport} from '../../../../app/src/lib/healthProfiles';
import {useWomenRecords,womenPages} from './womenRecords';
import {WomenDiary} from './WomenPages';
import './women-sharing.css';

export function SharedWomenInbox(){return <div className="wh-shared-workspace"><Link to="/customer/dashboard">← My health workspace</Link><SharedWomenList/></div>;}

export function SharedWomenList({doctor=false}:{doctor?:boolean}){
 const [items,setItems]=useState<{id:string;name:string}[]>([]),[error,setError]=useState('');
 useEffect(()=>{const load=()=>careApi<{items:{id:string;name:string}[]}>('/women/shared').then(d=>{setItems(d.items);setError('');}).catch(e=>{setItems([]);setError(e.message);});void load();const timer=setInterval(()=>void load(),30000);return()=>clearInterval(timer);},[]);
 return <section className="ch-panel"><h2>Women profiles shared with you</h2><p>Open the tabs their owner has allowed you to view or edit.</p>{error&&<p role="alert">{error}</p>}<div className="wh-shared-list">{items.map(p=><Link key={p.id} to={(doctor?'/doctor/women/':'/customer/women/shared/')+p.id}>{p.name} → Open shared tabs</Link>)}</div>{!items.length&&!error&&<p>No active shared Women profiles.</p>}</section>;
}

type Report={id:string;name:string;created_at:string;category:string};
function SharedReports({profileId,editable}:{profileId:string;editable:boolean}){
 const [items,setItems]=useState<Report[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const path='/women/profiles/'+profileId+'/reports';
 const load=async()=>{const data=await careApi<{items:Report[]}>(path);setItems(data.items);};
 useEffect(()=>{void load().catch(e=>setError(e.message));},[path]);
 return <section className="ch-panel"><h2>Medical records</h2><p>{editable?'You can view, upload and delete reports.':'View-only access to uploaded reports.'}</p>{editable&&<label>Upload report · PDF/JPG/PNG/WebP · up to 10 MB<input type="file" disabled={busy} accept="application/pdf,image/jpeg,image/png,image/webp" onChange={async e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;setError('');if(file.size>10485760||file.size===0){setError('Choose a non-empty file up to 10 MB.');return;}setBusy(true);try{const form=new FormData();form.append('file',file);await careApi(path,form);await load();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}/></label>}{items.map(r=><article className="wh-share-report" key={r.id}><span>{r.name}<small> · {r.category}</small></span><button disabled={busy} onClick={()=>void downloadReport({id:r.id,name:r.name,addedAt:r.created_at,downloadPath:'/api/v1'+path+'/'+r.id+'/download'}).catch(e=>setError(e.message))}>Download</button>{editable&&<button disabled={busy} onClick={async()=>{if(!confirm('Delete this report?'))return;setBusy(true);try{await careApi(path+'/'+r.id,undefined,true,'DELETE');await load();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>Delete</button>}</article>)}{error&&<p role="alert">{error}</p>}{!items.length&&!error&&<p>No reports uploaded.</p>}</section>;
}

export default function SharedWomenWorkspace(){
 const {profileId=''}=useParams();const store=useWomenRecords('',profileId);const [tab,setTab]=useState('dashboard');const doctor=location.pathname.startsWith('/doctor');
 const data=store.workspace;const visible=womenPages.filter(([id])=>Boolean(data?.permissions[id]));
 return <div className="wh-shared-workspace wh-app"><Link to={doctor?'/doctor/patients':'/customer/dashboard'}>← Back to {doctor?'patients':'family'}</Link>{!data?<section className="ch-panel"><h1>Shared Women workspace</h1><p role={store.error?'alert':'status'}>{store.error||'Loading permitted tabs…'}</p><button onClick={()=>void store.refresh().catch(()=>{})}>Refresh access</button></section>:<><div className="ch-page-heading"><div><h1>{data.profile.name} · Women’s Health</h1><p>Only the tabs shared with your account appear here. Access ends automatically at expiry.</p></div><button onClick={()=>void store.refresh().catch(()=>{})}>Refresh</button></div><nav aria-label="Shared women tabs"><button aria-pressed={tab==='dashboard'} onClick={()=>setTab('dashboard')}>Dashboard</button>{visible.map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label} · {data.permissions[id]==='edit'?'View + Edit':'View'}</button>)}</nav>{tab==='dashboard'?<section className="ch-panel"><h2>Shared overview</h2><div className="wh-shared-overview">{visible.map(([id,label])=><button key={id} onClick={()=>setTab(id)}><strong>{label}</strong><small>{id==='records'?'Open shared reports':store.records.filter(r=>r.section===id).length+' diary entries'} · {data.permissions[id]==='edit'?'View + Edit':'View only'}</small></button>)}</div></section>:!data.permissions[tab]?<p role="alert">This tab is no longer shared.</p>:tab==='records'?<SharedReports key={profileId+data.permissions[tab]} profileId={profileId} editable={data.permissions[tab]==='edit'}/>:<WomenDiary key={profileId+tab+data.permissions[tab]} section={tab} store={store} readOnly={data.permissions[tab]!=='edit'}/>}</>}{store.error&&data&&<p role="alert">{store.error}</p>}</div>;
}
