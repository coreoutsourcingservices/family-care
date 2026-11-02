import {useEffect,useState,type ReactNode} from 'react';
import {useLocation,useNavigate} from 'react-router-dom';
import {authApi} from '../lib/authApi';
export default function MemberRouteGuard({children}:{children:ReactNode}){
 const location=useLocation(),navigate=useNavigate();const [checked,setChecked]=useState('');
 const publicPage=['/customer/login','/customer/signup','/customer/family-invite'].includes(location.pathname)||!location.pathname.startsWith('/customer');
 useEffect(()=>{if(publicPage)return;let active=true;authApi('/patients/me',undefined,'GET').then(data=>{if(!active)return;const user=data.user;if(user?.is_family_member&&user.member_module&&user.member_profile_id){document.documentElement.dataset.memberModule=user.member_module;sessionStorage.setItem('familycare.selected'+(user.member_module==='adult'?'Adult':'Woman')+'.'+user.id,user.member_profile_id);if(!location.pathname.startsWith('/customer/'+user.member_module+'/')||new URLSearchParams(location.search).get('add')==='1'){navigate(user.redirect_url!,{replace:true});return;}}else delete document.documentElement.dataset.memberModule;setChecked(location.pathname);}).catch(()=>{if(active)setChecked(location.pathname);});return()=>{active=false;};},[location.pathname,location.search,publicPage,navigate]);
 return publicPage||checked===location.pathname?<>{children}</>:<p className="customer-session-status" role="status">Opening your health profile…</p>;
}
