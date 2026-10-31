'use client';
import {createContext,useCallback,useContext,useEffect,useState,type ReactNode} from 'react';
import {api} from '@/lib/api';
export type NetworkPerson={id:string;public_id:string;full_name:string;email:string;role:string;approval_status:string;account_status:string;created_at:string;can_review?:boolean};
export type DashboardData={as_of:string;approved_doctors?:number;metrics:Record<'administrators'|'doctors'|'patients'|'children',{total:number;this_month:number}>;
 monthly_growth:{month:string;patients:number;doctors:number;administrators:number}[];
 recent_registrations:NetworkPerson[];pending_requests:{total:number;items:NetworkPerson[]};
 recent_activities:{id:string;action:string;person:string;created_at:string}[];
 child_care:{total_children:number;active_guides:number;inactive_guides:number;growth_records:number;nutrition_records:number;vaccination_records:number}};
const Context=createContext<{data?:DashboardData;loading:boolean;error:string;refresh:()=>Promise<void>}>({loading:true,error:'',refresh:async()=>{}});
export function SuperadminDataProvider({children,scope='superadmin'}:{children:ReactNode;scope?:'admin'|'superadmin'}){
 const [data,setData]=useState<DashboardData>(),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const refresh=useCallback(async()=>{setLoading(true);setError('');try{const result=await api<DashboardData>(scope+'/dashboard');if(!result.metrics)throw Error('Dashboard update is starting. Please refresh shortly.');setData(result);}catch(e){setError((e as Error).message);}finally{setLoading(false);}},[scope]);
 useEffect(()=>{void refresh();},[refresh]);
 return <Context.Provider value={{data,loading,error,refresh}}>{children}</Context.Provider>;
}
export const useSuperadminData=()=>useContext(Context);
export const personLink=(p:NetworkPerson)=>p.role==='PATIENT'?'/superadmin/patients/'+p.id:p.role==='DOCTOR'?'/superadmin/doctors/'+p.public_id:'/superadmin/admins?search='+encodeURIComponent(p.email);
export function relativeTime(value:string){const seconds=Math.max(0,(Date.now()-new Date(value).getTime())/1000);if(seconds<60)return 'Just now';if(seconds<3600)return Math.floor(seconds/60)+' min ago';if(seconds<86400)return Math.floor(seconds/3600)+' hours ago';return Math.floor(seconds/86400)+' days ago';}
