import type { ModuleId } from '../components/ModuleSelector';
import { careApi } from './careApi';
import { ApiError, authApi, refreshSession, publicPortal } from './authApi';
export type EmergencyContact = { id: string; name: string; mobile: string };
export type ReferralDoctor = { photo?:{url:string;name:string}|null; code: string; name: string; qualification: string | null; specialization: string | null; email?:string; mobile?:string; id?:string; publicId?:string; photoUrl?:string|null; council?:string; clinicAddress?:string; experience?:number };
export type Referral = { type: 'self' | 'doctor'; code: string; doctor?: ReferralDoctor | null };
export type HealthReport = { id: string; name: string; category?:string; categoryReviewed?:boolean; blob?: Blob; size?: number; addedAt: string; downloadPath?: string };
export type HealthProfile = { id: string; ownerId: string; module: ModuleId; name: string; dob: string; guardianContact: string; guardianName?:string; contacts: EmergencyContact[]; reports: HealthReport[]; referral: Referral; createdAt: string; updatedAt: string; profileType: 'self' | 'member'; memberEmail: string; locked?: boolean; canEdit?: boolean };
type RemoteReport = { id: string; name: string; category?:string; category_reviewed?:boolean; size_bytes?: number; created_at: string };
export type RemoteProfile = { id: string; module: ModuleId; full_name: string; date_of_birth?: string; guardian_contact?: string; guardian_name?:string; emergency_contacts?: { name: string; mobile_number: string }[]; doctor?: { photo?:{url:string;name:string}|null; referral_id: string; full_name: string; email?:string; mobile_number?:string; id?:string; public_id?:string; qualification?:string; specialization?:string; registering_council?:string; clinic_address?:string; years_of_experience?:number; profile_photo_url?:string|null }; reports?: RemoteReport[]; created_at: string; profile_type: 'self' | 'member'; member_email?: string; locked?: boolean; can_edit?: boolean };
export function fromRemote(profile: RemoteProfile, doctor = false): HealthProfile {
  const prefix = doctor ? '/doctors/care-profiles/' : '/patients/profiles/';
  return { id: profile.id, ownerId: '', module: profile.module, name: profile.full_name, dob: profile.date_of_birth ?? '', guardianContact: profile.guardian_contact ?? '', guardianName:profile.guardian_name??'', contacts: (profile.emergency_contacts ?? []).map((c,i)=>({ id: String(i),name:c.name,mobile:c.mobile_number })), reports:(profile.reports??[]).map(r=>({id:r.id,name:r.name,category:r.category,categoryReviewed:r.category_reviewed,size:r.size_bytes,addedAt:r.created_at,downloadPath:`/api/v1${prefix}${profile.id}/reports/${r.id}/download`})), referral:{type:profile.doctor?'doctor':'self',code:profile.doctor?.referral_id??'',doctor:profile.doctor?{code:profile.doctor.referral_id,photo:profile.doctor.photo,name:profile.doctor.full_name,qualification:profile.doctor.qualification??null,specialization:profile.doctor.specialization??null,email:profile.doctor.email,mobile:profile.doctor.mobile_number,id:profile.doctor.id,publicId:profile.doctor.public_id,photoUrl:profile.doctor.profile_photo_url,council:profile.doctor.registering_council,clinicAddress:profile.doctor.clinic_address,experience:profile.doctor.years_of_experience}:null},createdAt:profile.created_at,updatedAt:profile.created_at,profileType:profile.profile_type,memberEmail:profile.member_email??'',locked:profile.locked,canEdit:profile.can_edit };
}
export async function loadProfiles(_ownerId:string,module:ModuleId):Promise<HealthProfile[]> {
  const profiles=await listAll<RemoteProfile>(`/patients/profiles?module=${module}`);
  return profiles.map(p=>fromRemote(p));
}
async function listAll<T>(path: string): Promise<T[]> {
  const items: T[] = [];
  let page = 1;
  while (true) {
    const data = await careApi<{items:T[];total?:number}>(`${path}${path.includes('?') ? '&' : '?'}page=${page}&per_page=100`);
    items.push(...data.items);
    if (data.items.length < 100 || data.total !== undefined && items.length >= data.total) return items;
    page++;
  }
}
export async function loadProfile(id:string, doctor=false):Promise<HealthProfile> {
  const prefix=doctor?'/doctors/care-profiles':'/patients/profiles';
  const detail=await careApi<{profile:RemoteProfile}>(`${prefix}/${id}`);
  const reports=await listAll<RemoteReport>(`${prefix}/${id}/reports`);
  return fromRemote({...detail.profile,reports},doctor);
}
export async function selfProfile():Promise<{profile:HealthProfile|null;account:{full_name:string;email:string;mobile_number:string}}> {
  const [session, profiles] = await Promise.all([authApi('/patients/me',undefined,'GET'),listAll<RemoteProfile>('/patients/profiles')]);
  if(!session.user)throw Error('Please sign in again to load your account.');
  const own=profiles.find(profile=>profile.profile_type==='self');
  return {profile:own?await loadProfile(own.id):null,account:{full_name:session.user.full_name,email:session.user.email??'',mobile_number:session.user.phone_number??''}};
}
function metadata(profile:HealthProfile):Record<string,unknown> {
  return {profile_type:profile.profileType,module:profile.module,full_name:profile.name,...(profile.dob?{date_of_birth:profile.dob}:{}),guardian_contact:profile.guardianContact,guardian_name:profile.guardianName??'',emergency_contacts:profile.contacts.map(c=>({name:c.name,mobile_number:c.mobile,relationship:'Emergency contact'})),...(profile.referral.type==='doctor'?{referral_id:profile.referral.code}:{})};
}
export class PartialSaveError extends Error { constructor(message:string,public profile:HealthProfile){super(message);} }
export async function saveProfile(profile:HealthProfile):Promise<HealthProfile> {
  const payload=metadata(profile);
  const isNew=profile.id.startsWith('new-');
  let saved:HealthProfile;
  if(isNew){const data=await careApi<{profile:RemoteProfile}>('/patients/profiles',payload);saved=fromRemote(data.profile);}
  else{saved=await loadProfile(profile.id);}
  if(saved.locked)return saved;
  for(const report of profile.reports.filter(r=>r.blob)) {
    const form=new FormData();form.append('file',report.blob!,report.name);
    try {const result=await careApi<{report:RemoteReport}>(`/patients/profiles/${saved.id}/reports`,form);saved={...saved,reports:[...saved.reports,{id:result.report.id,name:result.report.name,size:result.report.size_bytes,addedAt:result.report.created_at,downloadPath:`/api/v1/patients/profiles/${saved.id}/reports/${result.report.id}/download`}]};}
    catch(error){throw new PartialSaveError(error instanceof Error?error.message:'Report upload failed',saved);}
  }
  return saved;
}
export function reportUrl(report:HealthReport){return`${import.meta.env.VITE_API_BASE_URL??''}${report.downloadPath??''}`;}
export async function downloadReport(report:HealthReport,retry=true):Promise<void>{
  const response=await fetch(reportUrl(report),{credentials:'include',headers:{'X-Auth-Transport':'cookie','X-Requested-With':'FamilyCare','X-FamilyCare-Portal':publicPortal()}});
  if(!response.ok){const data=await response.json();if(response.status===401&&data.error?.code==='invalid_token'&&retry){await refreshSession();return downloadReport(report,false);}throw new ApiError(data.error?.message??'Unable to download report',data.error?.code??'download_failed',response.status);}
  let url:string;let revoke=false;
  if(response.headers.get('content-type')?.includes('application/json')){const data=await response.json();url=data.report.url;const parsed=new URL(url);if(parsed.protocol!=='https:'||!['res.cloudinary.com','api.cloudinary.com'].includes(parsed.hostname))throw Error('Report download is unavailable.');}
  else{url=URL.createObjectURL(await response.blob());revoke=true;}
  const link=document.createElement('a');link.href=url;link.download=report.name;link.target='_blank';link.rel='noopener noreferrer';link.click();if(revoke)window.setTimeout(()=>URL.revokeObjectURL(url),60000);
}

export async function updateHealthProfile(profile:HealthProfile):Promise<HealthProfile>{
 const result=await careApi<{profile:RemoteProfile}>('/patients/profiles/'+profile.id,{full_name:profile.name,date_of_birth:profile.dob,guardian_name:profile.guardianName??'',guardian_contact:profile.guardianContact,emergency_contacts:profile.contacts.map(c=>({name:c.name,mobile_number:c.mobile,relationship:'Emergency contact'}))},true,'PATCH');
 return {...fromRemote(result.profile),reports:profile.reports};
}
export async function removeHealthProfile(id:string){return careApi('/patients/profiles/'+id,undefined,true,'DELETE');}
