import { authApi } from '../../../../app/src/lib/authApi';
export type AdultRecord = { id:string; kind:string; title:string; date:string; notes:string; status:string; context?:string; systolic?:number|null; diastolic?:number|null; pulse?:number|null; glucose?:number|null; total?:number|null; ldl?:number|null; hdl?:number|null; triglycerides?:number|null; minutes?:number|null };
export const adultPages = [['dashboard','Dashboard'],['bp','Blood pressure'],['glucose','Blood sugar'],['lipids','Cholesterol'],['medicine','Medicines'],['lifestyle','Lifestyle'],['screening','Preventive care'],['history','Medical history'],['reports','Health reports'],['consultation_request','Doctor consultation'],['reminder','Reminders'],['settings','My profile']] as const;
export async function adultRecords(id:string) { const result=await authApi('/patients/adults/'+id+'/records',undefined,'GET') as unknown as {items:AdultRecord[]};return result.items; }
export async function saveAdult(id:string, values:Record<string,unknown>,recordId?:string) {return authApi('/patients/adults/'+id+'/records'+(recordId?'/'+recordId:''),values);}
export async function deleteAdult(id:string,recordId:string){return authApi('/patients/adults/'+id+'/records/'+recordId+'/delete',{});}
export function today(){return new Date().toLocaleDateString('en-CA');}
