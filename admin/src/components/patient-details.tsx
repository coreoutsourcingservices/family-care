'use client';
import {useCallback, useEffect, useState} from 'react';
import Link from 'next/link';
import {ArrowLeft, ArrowRight, Baby, Heart, Users, RefreshCw, LoaderCircle, UserRound} from 'lucide-react';
import {api} from '@/lib/api';
import {apiRole, rolePath, type ProfileCounts, type Role, type User} from '@/lib/types';
import {useUiTranslation} from '@/lib/i18n';

type Member={id:string;full_name:string;profile_type:'self'|'member';module:'child'|'adult'|'women';date_of_birth:string;guardian_contact?:string;created_at:string;report_count:number;parent_name?:string;emergency_contacts:{name:string;mobile_number:string;relationship?:string}[];doctor?:{full_name:string;referral_id:string;email?:string;mobile_number?:string}|null};
type Account={user:User&{created_at:string};profile_counts:ProfileCounts};
type Members={items:Member[];total:number};
const moduleNames:Record<string,string>={child:'Child care',adult:'Adult health',women:"Women's health"};
const moduleLabel=(module:string)=>moduleNames[module]??module;
const displayDate=(value:string)=>value?new Date(value.length===10?value+'T00:00:00':value).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):'Not entered';

export default function PatientDetails({role,patientId,profileId}:{role:Role;patientId:string;profileId?:string}){
 const {t}=useUiTranslation();
 const [account,setAccount]=useState<Account>();const [list,setList]=useState<Members>({items:[],total:0});const [member,setMember]=useState<Member>();
 const [page,setPage]=useState(1),[module,setModule]=useState(''),[loading,setLoading]=useState(true),[error,setError]=useState(''),[version,setVersion]=useState(0);
 const root=`${rolePath(role)}/patients`,accountPath=`${root}/${encodeURIComponent(patientId)}`,endpoint=`${apiRole(role)}/patients/${encodeURIComponent(patientId)}`;
 const refresh=useCallback(()=>setVersion(v=>v+1),[]);
 useEffect(()=>{let active=true;setLoading(true);setError('');
  Promise.all([api<Account>(endpoint),profileId?api<{profile:Member}>(`${endpoint}/profiles/${encodeURIComponent(profileId)}`):api<Members>(`${endpoint}/profiles?page=${page}&per_page=20${module?'&module='+module:''}`)])
   .then(([account,result])=>{if(!active)return;setAccount(account);if('profile' in result)setMember(result.profile);else setList(result);})
   .catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoading(false);});
  return()=>{active=false;};
 },[endpoint,profileId,page,module,version]);
 return <>
  <Link className="text-link patient-back" href={profileId?accountPath:root}><ArrowLeft size={16}/>{t(profileId?'Back to family profiles':'Back to patients')}</Link>
  <div className="page-heading"><div><p className="eyebrow">{t('PATIENTS / FAMILY PROFILES')}</p><h1>{profileId?t('Member details'):t('Patient & family')}<span className="teal">.</span></h1><p>{t(profileId?'Profile details and the account that added this member.':'See the account owner and every profile they have added.')}</p></div><button className="secondary" onClick={refresh} disabled={loading} aria-label={t('Refresh details')}><RefreshCw size={16} className={loading?'spin':''}/>{t('Refresh')}</button></div>
  {loading?<section className="card patient-loading" role="status"><LoaderCircle className="spin"/>{t('Loading patient details...')}</section>:error?<div className="alert error" role="alert">{t(error)} <button className="text-button" onClick={refresh}>{t('Try again')}</button></div>:account&&<>
   <section className="card patient-owner-card"><div className="patient-owner-icon"><UserRound size={27}/></div><div><span className="eyebrow">{t('ACCOUNT OWNER')}</span><h2>{account.user.full_name}</h2><p>{account.user.email}</p><small>{account.user.public_id}{account.user.phone_number?' · '+account.user.phone_number:''}</small></div><div className="patient-owner-meta"><span className={`badge ${account.user.approval_status==='APPROVED'?'approved':'pending'}`}>{t(account.user.approval_status)}</span><span className="account-state">{t(account.user.account_status)}</span><small>{t('Joined')} {displayDate(account.user.created_at)}</small></div></section>
   {profileId&&member?<>
    <section className="card patient-member-card"><div className="patient-detail-heading"><div><span className="eyebrow">{t(moduleLabel(member.module))}</span><h2>{member.full_name}</h2></div><span className={`badge ${member.profile_type==='self'?'approved':'pending'}`}>{t(member.profile_type==='self'?'Self profile':'Family member')}</span></div><p className="patient-added-by">{t('Added by')} <Link href={accountPath}>{account.user.full_name}</Link></p>
     <dl className="patient-detail-grid"><Field label={t('Profile ID')} value={member.id}/><Field label={t('Profile type')} value={t(member.profile_type==='self'?'Account owner’s own profile':'Member added to this account')}/><Field label={t('Date of birth')} value={displayDate(member.date_of_birth)}/><Field label={t('Care area')} value={t(moduleLabel(member.module))}/><Field label={t('Guardian contact')} value={member.guardian_contact||t('Not entered')}/><Field label={t('Linked parent profile')} value={member.parent_name||t('Not linked')}/><Field label={t('Uploaded reports')} value={String(member.report_count)}/><Field label={t('Profile added')} value={displayDate(member.created_at)}/></dl>
    </section>
    <div className="patient-support-grid"><section className="card patient-member-card"><h2>{t('Connected doctor')}</h2>{member.doctor?<dl className="patient-detail-grid"><Field label={t('Name')} value={member.doctor.full_name}/><Field label={t('Referral ID')} value={member.doctor.referral_id}/><Field label={t('Email')} value={member.doctor.email||t('Not entered')}/><Field label={t('Mobile number')} value={member.doctor.mobile_number||t('Not entered')}/></dl>:<p className="patient-muted">{t('No doctor connected to this profile.')}</p>}</section><section className="card patient-member-card"><h2>{t('Emergency contacts')}</h2>{member.emergency_contacts.length?member.emergency_contacts.map((contact,index)=><div className="patient-contact" key={index}><strong>{contact.name}</strong><span>{contact.mobile_number}</span>{contact.relationship&&<small>{contact.relationship}</small>}</div>):<p className="patient-muted">{t('No emergency contacts added.')}</p>}</section></div>
   </>:<>
    <div className="patient-count-grid">{[{label:'Family members',value:account.profile_counts.members,Icon:Users},{label:'Self profiles',value:account.profile_counts.self,Icon:UserRound},{label:'Child profiles',value:account.profile_counts.child,Icon:Baby},{label:'Adult profiles',value:account.profile_counts.adult,Icon:Users},{label:'Women profiles',value:account.profile_counts.women,Icon:Heart}].map(({label,value,Icon})=><section className="card patient-count" key={label}><Icon size={20}/><span>{t(label)}<strong>{value}</strong></span></section>)}</div>
    <section className="card directory-card"><div className="directory-toolbar"><div><div className="title-row"><h2>{t('All family profiles')}</h2><span className="count-badge">{account.profile_counts.total}</span></div><p className="patient-muted">{t('Self profiles and members added by this account owner.')}</p></div><label className="patient-filter">{t('Care area')}<select aria-label={t('Filter family profiles')} value={module} onChange={e=>{setModule(e.target.value);setPage(1);}}><option value="">{t('All care areas')}</option><option value="child">{t('Child care')}</option><option value="adult">{t('Adult health')}</option><option value="women">{t("Women's health")}</option></select></label></div>
     <div className="table-scroll"><table><thead><tr><th>{t('Profile name')}</th><th>{t('Profile type')}</th><th>{t('Care area')}</th><th>{t('Date of birth')}</th><th>{t('Reports')}</th><th>{t('Details')}</th></tr></thead><tbody>{list.items.map(profile=><tr key={profile.id}><td><Link className="patient-account-link" href={`${accountPath}/profiles/${profile.id}`}>{profile.full_name}</Link></td><td><span className={`badge ${profile.profile_type==='self'?'approved':'pending'}`}>{t(profile.profile_type==='self'?'Self':'Member')}</span></td><td>{t(moduleLabel(profile.module))}</td><td>{displayDate(profile.date_of_birth)}</td><td>{profile.report_count}</td><td><Link className="text-link" href={`${accountPath}/profiles/${profile.id}`} aria-label={t('View profile')+' '+profile.full_name}>{t('View profile')}<ArrowRight size={14}/></Link></td></tr>)}{!list.items.length&&<tr><td colSpan={6}><div className="table-empty"><Users/><h3>{t(module?'No profiles in this care area':'No profiles added yet')}</h3><p>{t('Profiles will appear here when this patient adds them.')}</p></div></td></tr>}</tbody></table></div>
     <div className="pagination"><span>{list.total} {t('profiles')} · {t('Page')} {page}</span><div><button className="secondary small" disabled={page===1} onClick={()=>setPage(p=>p-1)}>{t('Previous')}</button><button className="secondary small" disabled={page*20>=list.total} onClick={()=>setPage(p=>p+1)}>{t('Next')}</button></div></div>
    </section>
   </>}
  </>}
 </>;
}
function Field({label,value}:{label:string;value:string}){return <div><dt>{label}</dt><dd>{value}</dd></div>;}
