import { careApi } from '../../../../app/src/lib/careApi';
import { ApiError } from '../../../../app/src/lib/authApi';
import ReportTextPanel from '../../../../app/src/components/ReportTextPanel';
import { useEffect, useId, useRef, useState } from 'react';
import { FileText, UploadCloud, ArrowDownToLine, Image, Trash2, X, CheckCircle2, RotateCcw } from 'lucide-react';
import { downloadReport, type HealthProfile } from '../../../../app/src/lib/healthProfiles';
import './child-report-upload.css';

const types=['All','Doctor report','Lab tests','Prescriptions','Scans','Vaccination','Others'];
const categoryLabel=(category:string)=>category==='Scans'?'X-ray / imaging':category==='Lab tests'?'Lab report':category;
type UploadItem={id:string;file:File;category:string;status:'ready'|'uploading'|'uploaded'|'failed';error?:string;warning?:string};
type UploadResponse={report:{id:string};text_extraction?:{status:string;message?:string}};
function invalidFile(file:File){
 if(!file.size)return 'This file is empty. Choose a non-empty report.';
 if(file.size>10*1024*1024)return 'This file exceeds 10 MB. Split or compress this report.';
 const allowed=['application/pdf','image/jpeg','image/png','image/webp'];
 if(!allowed.includes(file.type)&&!((!file.type||file.type==='application/octet-stream')&&/\.(pdf|jpe?g|png|webp)$/i.test(file.name)))return 'Choose a PDF, JPG, PNG or WebP report.';
 return '';
}

export default function ChildHealthReports({profile,onRefresh}:{profile:HealthProfile;onRefresh:()=>Promise<void>}){
 const [reviewReport,setReviewReport]=useState(''),[chooseUpload,setChooseUpload]=useState(false),[uploadCategory,setUploadCategory]=useState('Doctor report');
 const [deleting,setDeleting]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(''),[filter,setFilter]=useState('All'),[search,setSearch]=useState('');
 const [queue,setQueue]=useState<UploadItem[]>([]),[progress,setProgress]=useState({done:0,total:0});
 const inputId=useId(),mounted=useRef(true),running=useRef(false),refresh=useRef(onRefresh);refresh.current=onRefresh;
 useEffect(()=>{
  mounted.current=true;setLoading(true);
  void refresh.current().catch(e=>{if(mounted.current)setError(e.message);}).finally(()=>{if(mounted.current)setLoading(false);});
  const reload=(event:Event)=>{if((event as CustomEvent).detail?.profileId===profile.id)void refresh.current().catch(e=>{if(mounted.current)setError(e.message);});};
  window.addEventListener('familycare:records-updated',reload);
  return()=>{mounted.current=false;window.removeEventListener('familycare:records-updated',reload);};
 },[profile.id]);
 function selectFiles(files:File[]){
  const next=files.map(file=>{const reason=invalidFile(file);return {id:crypto.randomUUID(),file,category:uploadCategory,status:reason?'failed':'ready',error:reason||undefined} as UploadItem;});
  setQueue(previous=>[...previous,...next]);setError('');setProgress({done:0,total:0});
 }
 async function save(items=queue){
  if(running.current)return;
  const selected=items.filter(item=>item.status!=='uploaded'&&!invalidFile(item.file));
  if(!selected.length)return;
  running.current=true;setBusy(true);setError('');setProgress({done:0,total:selected.length});
  let successes=0,lastReview='';
  try{
   for(const [index,item] of selected.entries()){
    if(!mounted.current)break;
    setQueue(previous=>previous.map(row=>row.id===item.id?{...row,status:'uploading',error:undefined,warning:undefined}:row));
    try{
     const form=new FormData();form.append('file',item.file);form.append('category',item.category);form.append('auto_read','true');
     let language='en';try{language=localStorage.getItem('familycare_report_source_language')||'en';}catch{/* File storage works without browser storage. */}
     form.append('source_language',language);
     const uploaded=await careApi<UploadResponse>('/patients/profiles/'+profile.id+'/reports',form);
     successes++;
     if(uploaded.text_extraction?.status==='QUEUED')lastReview=uploaded.report.id;
     if(mounted.current)setQueue(previous=>previous.map(row=>row.id===item.id?{...row,status:'uploaded',warning:uploaded.text_extraction?.message}:row));
    }catch(failure){
     if(mounted.current)setQueue(previous=>previous.map(row=>row.id===item.id?{...row,status:'failed',error:failure instanceof Error?failure.message:'Upload failed. Please retry this file.'}:row));
     if(failure instanceof ApiError&&failure.status===429){
      if(mounted.current){setError('The upload rate limit was reached. Wait one minute, then upload the remaining reports. Successful files are already saved.');setProgress({done:index+1,total:selected.length});}
      break;
     }
    }
    if(mounted.current)setProgress({done:index+1,total:selected.length});
   }
   if(mounted.current&&successes){
    setFilter('All');setSearch('');setReviewReport(lastReview);
    try{await refresh.current();}catch{if(mounted.current)setError('Reports uploaded, but the saved list could not refresh. Refresh the list below; do not upload the successful files again.');}
   }
  }finally{running.current=false;if(mounted.current)setBusy(false);}
 }
 async function chooseCategory(id:string,category:string){
  setBusy(true);setError('');try{await careApi('/patients/profiles/'+profile.id+'/reports/'+id+'/category',{category},true,'PATCH');await refresh.current();setReviewReport(category==='Scans'?'':id);}catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 async function removeReport(id:string){
  setBusy(true);setError('');try{await careApi('/patients/profiles/'+profile.id+'/reports/'+id,undefined,true,'DELETE');setReviewReport('');setDeleting('');await refresh.current();window.dispatchEvent(new CustomEvent('familycare:records-updated',{detail:{profileId:profile.id}}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 const visible=profile.reports.filter(report=>(filter==='All'||(report.category??'Others')===filter)&&(report.name+' '+(report.title??'')).toLowerCase().includes(search.toLowerCase()));
 const remaining=queue.filter(item=>item.status!=='uploaded'&&!invalidFile(item.file));
 const uploadedCount=queue.filter(item=>item.status==='uploaded').length,failedCount=queue.filter(item=>item.status==='failed').length;
 return <>
  <div className="ch-page-heading"><div><h1>Health reports</h1><p>Upload and download reports saved to {profile.name}'s account profile.</p></div><button className="ch-button" disabled={busy} onClick={()=>setChooseUpload(true)}><UploadCloud size={17}/>Upload reports</button></div>
  {chooseUpload&&<section className="cr-uploader ch-panel" aria-label="Upload multiple reports">
   <div className="cr-upload-heading"><div><h2>Add health reports</h2><p>Select multiple files together, or add more to the queue. Each report is saved separately.</p></div><button type="button" className="ch-icon-button" aria-label="Close upload panel" disabled={busy} onClick={()=>setChooseUpload(false)}><X size={19}/></button></div>
   <label className="cr-category">Category for new files<select value={uploadCategory} disabled={busy} onChange={event=>setUploadCategory(event.target.value)}>{types.slice(1).map(type=><option key={type} value={type}>{categoryLabel(type)}</option>)}</select></label>
   <div className="cr-dropzone" onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();if(!busy)selectFiles(Array.from(event.dataTransfer.files));}}>
    <UploadCloud size={29}/><strong>Drop reports here or choose files</strong><p>PDF, JPG, PNG or WebP. Up to 10 MB per file.</p>
    <label htmlFor={inputId}>Choose report files</label><input id={inputId} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp" disabled={busy} onChange={event=>{const files=Array.from(event.target.files??[]);event.target.value='';selectFiles(files);}}/>
   </div>
   <p className="cr-reading-note">Your original files are saved first. Text reports can be read when the reader is available; review extracted text before importing medical records. X-ray / imaging skips text reading.</p>
   {queue.length>0&&<><ul className="cr-upload-queue">{queue.map(item=><li key={item.id} data-status={item.status}>
    <FileText size={21}/><div className="cr-file-info"><strong>{item.file.name}</strong><small>{(item.file.size/1048576).toFixed(2)} MB</small>{item.error&&<p className="cr-file-error">{item.error}</p>}{item.warning&&<p>{item.warning}</p>}</div>
    <label className="cr-file-category"><span className="sr-only">Category for queued file {item.file.name}</span><select disabled={busy||item.status==='uploaded'} value={item.category} onChange={event=>setQueue(previous=>previous.map(row=>row.id===item.id?{...row,category:event.target.value}:row))}>{types.slice(1).map(type=><option key={type} value={type}>{categoryLabel(type)}</option>)}</select></label>
    <span className="cr-file-status">{item.status==='uploaded'?<><CheckCircle2 size={15}/>Uploaded</>:item.status==='uploading'?'Uploading...':item.status==='failed'?'Needs attention':'Ready'}</span>
    {item.status==='failed'&&!invalidFile(item.file)&&<button type="button" disabled={busy} aria-label={'Retry '+item.file.name} className="ch-icon-button" onClick={()=>void save([item])}><RotateCcw size={17}/></button>}
    {item.status!=='uploaded'&&<button type="button" disabled={busy} aria-label={'Remove '+item.file.name+' from upload queue'} className="ch-icon-button" onClick={()=>setQueue(previous=>previous.filter(row=>row.id!==item.id))}><X size={17}/></button>}
   </li>)}</ul><div className="cr-upload-actions"><p role="status" aria-live="polite">{busy?`Processing ${progress.done+1>progress.total?progress.total:progress.done+1} of ${progress.total} reports...`:`${uploadedCount} uploaded${failedCount?', '+failedCount+' need attention':''}`}</p><button type="button" className="ch-button" disabled={busy||!remaining.length} onClick={()=>void save()}><UploadCloud size={16}/>{busy?'Uploading...':`Upload ${remaining.length} ${remaining.length===1?'report':'reports'}`}</button>{uploadedCount>0&&<button type="button" className="ch-button secondary" disabled={busy} onClick={()=>setQueue(previous=>previous.filter(item=>item.status!=='uploaded'))}>Clear uploaded</button>}</div></>}
  </section>}
  <div className="ch-detail-toolbar"><div className="ch-tabs ch-filter-pills">{types.map(type=><button key={type} aria-pressed={filter===type} onClick={()=>setFilter(type)}>{type}</button>)}</div><input className="ch-search" aria-label="Search health reports" placeholder="Search reports..." value={search} onChange={e=>setSearch(e.target.value)}/></div>
  {error&&<p role="alert" className="ch-error">{error}<button type="button" className="ch-button secondary" onClick={()=>void refresh.current().then(()=>setError('')).catch(e=>setError(e.message))}>Refresh list</button></p>}
  {loading?<p role="status">Loading reports...</p>:visible.length?<div className="ch-reference-report-grid">{visible.map(report=><article key={report.id}>
   <button className="ch-report-preview" aria-label={'Open '+report.name} onClick={()=>void downloadReport(report).catch(e=>setError(e.message))}>{/\.(png|jpe?g|webp)$/i.test(report.name)?<Image size={44}/>:<FileText size={44}/>}<span>{report.name.split('.').at(-1)?.toUpperCase()??'FILE'}</span></button>
   <div><h3>{report.title||report.name}</h3>{report.title&&<small>{report.name}</small>}<label><span className="sr-only">Category for {report.name}</span><select disabled={busy} value={report.category??'Others'} onChange={e=>void chooseCategory(report.id,e.target.value)}>{types.slice(1).map(type=><option key={type} value={type}>{categoryLabel(type)}</option>)}</select></label><small>{report.addedAt?new Date(report.addedAt).toLocaleDateString('en-IN'):'Date not supplied'}</small>{report.size&&<small>{(report.size/1048576).toFixed(2)} MB</small>}
    <button className="ch-report-download" onClick={()=>void downloadReport(report).catch(e=>setError(e.message))}><ArrowDownToLine size={14}/>Open / download</button>
    {report.category==='Scans'?<p className="ch-report-imaging">Imaging file saved. Text extraction is skipped.</p>:<ReportTextPanel profileId={profile.id} report={report} initialOpen={report.id===reviewReport}/>}
    <button type="button" className="ch-report-delete" disabled={busy} onClick={()=>setDeleting(report.id)}><Trash2 size={15}/>Delete report</button>
    {deleting===report.id&&<div role="alertdialog" aria-label="Delete report confirmation"><p>Move this report, extracted text and linked imported records to the retained recycle bin? Manual entries stay saved.</p><button className="ch-report-delete" disabled={busy} onClick={()=>void removeReport(report.id)}>Confirm delete</button><button type="button" disabled={busy} onClick={()=>setDeleting('')}>Cancel</button></div>}
   </div></article>)}</div>:<section className="ch-panel"><div className="ch-empty"><FileText size={28}/><h3>{profile.reports.length?'No matching reports':'No reports uploaded yet'}</h3><p>PDF, JPG, PNG or WebP files up to 10 MB each. You can select several reports together.</p><button className="ch-button" disabled={busy} onClick={()=>setChooseUpload(true)}>Upload reports</button></div></section>}
 </>;
}
