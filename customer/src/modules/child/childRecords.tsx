import { useState, type FormEvent } from 'react';
import { Plus, Trash2, X } from 'lucide-react';
export type EntryKind='vaccination'|'history'|'growth'|'nutrition'|'consultation'|'care';
export type ChildEntry={id:string;kind:EntryKind;date:string;title:string;[key:string]:string};
export type Field={name:string;label:string;type?:string;required?:boolean;options?:string[];min?:string;max?:string};
export const localDate=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
export const formatDate=(date:string)=>date?new Date(date+'T00:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):'Not entered';
export function useChildRecords(accountId:string,profileId:string){
 const key=`familycare.child.v1.${accountId}.${profileId}`;
 const [error,setError]=useState('');
 const [entries,setEntries]=useState<ChildEntry[]>(()=>{try{const parsed=JSON.parse(localStorage.getItem(key)??'[]');return Array.isArray(parsed)?parsed.filter(e=>e&&typeof e.id==='string'&&typeof e.date==='string'&&typeof e.kind==='string'&&typeof e.title==='string'):[];}catch{return [];}});
 function persist(next:ChildEntry[]){try{localStorage.setItem(key,JSON.stringify(next));setEntries(next);setError('');return true;}catch{setError('Could not save on this device. Browser storage may be full or disabled.');return false;}}
 return {entries,error,add:(entry:ChildEntry)=>persist([...entries,entry]),remove:(id:string)=>persist(entries.filter(e=>e.id!==id))};
}
export function EntryForm({kind,fields,onAdd,label='Add record'}:{kind:EntryKind;fields:Field[];onAdd:(entry:ChildEntry)=>boolean;label?:string}){
 const [open,setOpen]=useState(false),[error,setError]=useState('');
 function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const values=Object.fromEntries(new FormData(event.currentTarget)) as Record<string,string>;if(!values.title?.trim()){setError('Enter a name for this record.');return;}if(kind==='vaccination'&&values.nextDate&&values.nextDate<values.date){setError('Next due date must be on or after the vaccination date.');return;}if(onAdd({...values,title:values.title.trim(),id:crypto.randomUUID(),kind} as ChildEntry)){setOpen(false);setError('');}}
 return <div className="ch-entry-area">{!open?<button className="ch-button" onClick={()=>setOpen(true)}><Plus size={17}/>{label}</button>:<form className="ch-entry-form" onSubmit={submit}><div className="ch-form-top"><h3>{label}</h3><button className="ch-icon-button" type="button" onClick={()=>setOpen(false)} aria-label="Close record form"><X size={18}/></button></div><div className="ch-form-grid">{fields.map(field=><label key={field.name}>{field.label}{field.required&&<b aria-hidden="true"> *</b>}{field.options?<select name={field.name} required={field.required}>{field.options.map(option=><option key={option}>{option}</option>)}</select>:field.type==='textarea'?<textarea name={field.name} maxLength={2000} rows={3}/>:<input name={field.name} type={field.type??'text'} required={field.required} min={field.min} max={field.max} step={field.type==='number'?'0.1':undefined} maxLength={field.type==='text'||!field.type?160:undefined} defaultValue={field.name==='date'?localDate():undefined}/>}</label>)}</div>{error&&<p role="alert" className="ch-error">{error}</p>}<div className="ch-form-actions"><button type="button" className="ch-button secondary" onClick={()=>setOpen(false)}>Cancel</button><button type="submit" className="ch-button">Save on this device</button></div></form>}</div>;
}
export function EntryList({entries,fields,onRemove,empty}:{entries:ChildEntry[];fields:{key:string;label:string}[];onRemove:(id:string)=>boolean;empty:string}){
 const [removeId,setRemoveId]=useState('');
 return entries.length?<div className="ch-record-list">{[...entries].sort((a,b)=>b.date.localeCompare(a.date)).map(entry=><article key={entry.id} className="ch-record"><div className="ch-record-date">{formatDate(entry.date)}</div><div className="ch-record-main"><h3>{entry.title}</h3><div className="ch-record-values">{fields.filter(f=>entry[f.key]).map(f=><p key={f.key}><span>{f.label}</span>{f.key==='nextDate'?formatDate(entry[f.key]):entry[f.key]}</p>)}</div></div>{removeId===entry.id?<div className="ch-remove-confirm"><span>Remove this record?</span><button onClick={()=>{onRemove(entry.id);setRemoveId('');}}>Remove</button><button onClick={()=>setRemoveId('')}>Cancel</button></div>:<button className="ch-icon-button" aria-label={'Remove '+entry.title} onClick={()=>setRemoveId(entry.id)}><Trash2 size={17}/></button>}</article>)}</div>:<div className="ch-empty"><span>+</span><h3>{empty}</h3><p>Add a record to start building your child's care timeline.</p></div>;
}
export const dateField:Field={name:'date',label:'Date',type:'date',required:true};
export type SectionProps={entries:ChildEntry[];onAdd:(entry:ChildEntry)=>boolean;onRemove:(id:string)=>boolean};
