import {createContext,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import {useLocation,useNavigate} from 'react-router-dom';
import {ApiError,authApi,type AuthUser} from '../lib/authApi';

const PatientSession=createContext<AuthUser|null>(null);
export const usePatientSession=()=>useContext(PatientSession);

export default function MemberRouteGuard({children}:{children:ReactNode}){
 const location=useLocation(),navigate=useNavigate();
 const [user,setUser]=useState<AuthUser|null>(null),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 const verifiedAt=useRef(0),navigation=useRef(navigate);navigation.current=navigate;
 const publicPage=['/customer/login','/customer/signup','/customer/family-invite'].includes(location.pathname)||!location.pathname.startsWith('/customer');
 // Preserve the workspace across internal navigation. Every backend request
 // still enforces authorization; returning to the tab revalidates the session.
 useEffect(()=>{
  if(publicPage){setUser(null);setError('');verifiedAt.current=0;delete document.documentElement.dataset.memberModule;return;}
  let active=true,running=false;
  async function verify(){
   if(running)return;running=true;
   try{
    const result=await authApi('/patients/me',undefined,'GET');
    if(!active)return;
    if(result.user?.role!=='PATIENT')throw new ApiError('Please sign in to your family account.','invalid_session',401);
    verifiedAt.current=Date.now();setUser(result.user);setError('');
   }catch(failure){
    if(!active)return;
    if(failure instanceof ApiError&&[401,403].includes(failure.status)){setUser(null);navigation.current('/customer/login',{replace:true});}
    else setError(failure instanceof Error?failure.message:'Unable to check your session.');
   }finally{running=false;}
  }
  void verify();
  const onFocus=()=>{if(Date.now()-verifiedAt.current>60000)void verify();};
  window.addEventListener('focus',onFocus);
  return()=>{active=false;window.removeEventListener('focus',onFocus);};
 },[publicPage,attempt]);
 const member=user?.is_family_member&&user.member_module&&user.member_profile_id?user:null;
 const shared=location.pathname.startsWith('/customer/women/shared')||location.pathname.startsWith('/customer/adult/shared');
 const redirectMember=!!member&&(!shared&&!location.pathname.startsWith('/customer/'+member.member_module+'/')||new URLSearchParams(location.search).get('add')==='1');
 useEffect(()=>{
  if(publicPage||!user)return;
  if(member){
   document.documentElement.dataset.memberModule=member.member_module!;
   sessionStorage.setItem('familycare.selected'+(member.member_module==='adult'?'Adult':'Woman')+'.'+member.id,member.member_profile_id!);
   if(redirectMember)navigate(member.redirect_url||'/customer/'+member.member_module+'/dashboard?profile='+member.member_profile_id,{replace:true});
  }else delete document.documentElement.dataset.memberModule;
 },[publicPage,user,member,redirectMember,navigate]);
 if(publicPage)return <>{children}</>;
 if(!user||redirectMember)return <div className="customer-session-status" role="status">{error?<><p role="alert">{error}</p><button onClick={()=>setAttempt(value=>value+1)}>Try again</button></>:'Opening your health profile...'}</div>;
 return <PatientSession.Provider value={user}>{error&&<p role="alert">{error}<button onClick={()=>setAttempt(value=>value+1)}>Retry session check</button></p>}{children}</PatientSession.Provider>;
}
