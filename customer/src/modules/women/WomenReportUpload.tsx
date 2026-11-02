import './women-report-upload.css';
import {useEffect,useState} from 'react';
import {UploadCloud,FileText} from 'lucide-react';
import {careApi} from '../../../../app/src/lib/careApi';
import {downloadReport,type HealthProfile,type HealthReport} from '../../../../app/src/lib/healthProfiles';
import ReportTextPanel from '../../../../app/src/components/ReportTextPanel';

export default function WomenReportUpload({profile,onRefresh,history=false}:{profile:HealthProfile;onRefresh:()=>Promise<void>;history?:boolean}){
 const [category,setCategory]=useState('Lab tests'),[language,setLanguage]=useState('en'),[read,setRead]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[uploaded,setUploaded]=useState<HealthReport[]>([]);
 useEffect(()=>{if(history)void onRefresh().catch(e=>setError((e as Error).message));},[profile.id,history]);
 async function upload(files:File[]){
  if(files.some(f=>!f.size||f.size>10485760||!['application/pdf','image/jpeg','image/png','image/webp'].includes(f.type))){setError('Choose PDF, JPG, PNG or WebP files up to 10 MB each.');return;}
  setBusy(true);setError('');
  try{for(const file of files){const form=new FormData();form.append('file',file);form.append('category',category);form.append('source_language',language);form.append('auto_read',String(read&&category!=='Scans'));
   const {report}=await careApi<{report:{id:string;name:string;created_at:string}}>(`/women/profiles/${profile.id}/reports`,form);
   setUploaded(old=>[{id:report.id,name:report.name,addedAt:report.created_at,category,downloadPath:`/api/v1/women/profiles/${profile.id}/reports/${report.id}/download`},...old]);}
   await onRefresh();
  }catch(e){setError((e as Error).message);await onRefresh().catch(()=>{});}finally{setBusy(false);}
 }
 const reports=history?Array.from(new Map([...uploaded,...profile.reports].map(r=>[r.id,r])).values()):uploaded;
 return <section className="ch-panel women-report-upload"><h2>Upload & read medical report</h2><p>Keep your reports and extracted text together in your private health records.</p><fieldset disabled={busy} className="wh-report-fields"><label className="wh-report-field">Report category<select value={category} onChange={e=>setCategory(e.target.value)}>{['Doctor report','Lab tests','Prescriptions','Scans','Vaccination','Others'].map(c=><option key={c}>{c}</option>)}</select></label><label className="wh-report-field">Document language<select value={language} onChange={e=>setLanguage(e.target.value)}>{[['en','English'],['hi','Hindi'],['mr','Marathi'],['ta','Tamil'],['te','Telugu'],['ur','Urdu'],['ar','Arabic'],['ne','Nepali'],['sa','Sanskrit'],['fr','French'],['de','German'],['es','Spanish'],['pt','Portuguese'],['ru','Russian']].map(([code,name])=><option key={code} value={code}>{name}</option>)}</select></label>{category!=='Scans'&&<label className="wh-report-auto"><input type="checkbox" checked={read} onChange={e=>setRead(e.target.checked)}/>Read report text automatically</label>}<label className="ch-report-upload"><UploadCloud/><strong>{busy?'Uploading...':'Choose medical report'}</strong><span>PDF, JPG, PNG, WebP · 10 MB per file · OCR up to 5 PDF pages</span><input aria-label="Upload medical reports" type="file" multiple accept="application/pdf,image/jpeg,image/png,image/webp" onChange={e=>{const files=Array.from(e.target.files??[]);e.target.value='';if(files.length)void upload(files);}}/></label></fieldset>{error&&<p role="alert">{error}</p>}{category==='Scans'&&<p>Imaging files are stored for your doctor to review; no scan interpretation is generated.</p>}<p className="wh-report-hint">Check extracted text against the original report. It can contain reading errors. Translation is optional and needs consent.</p>{reports.map(report=><div key={report.id}><button className="wh-task" onClick={()=>void downloadReport(report).catch(e=>setError(e.message))}><FileText/>{report.name}</button>{report.category!=='Scans'&&<ReportTextPanel profileId={profile.id} report={report} initialOpen={uploaded.some(r=>r.id===report.id)&&read}/>}</div>)}{history&&!reports.length&&<p>No reports uploaded yet.</p>}</section>;
}
