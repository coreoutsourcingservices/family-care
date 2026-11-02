import {ArrowLeft} from 'lucide-react';
import {useLocation,useNavigate} from 'react-router-dom';
import './customer-back.css';
export default function CustomerBack(){
 const location=useLocation(),navigate=useNavigate();
 if(!location.pathname.startsWith('/customer/')||/\/(?:login|signup|family-invite)$/.test(location.pathname))return null;
 return <div className="customer-floating-back-anchor"><button type="button" className="customer-floating-back" aria-label="Go back" onClick={()=>{const event=new Event('familycare:back',{cancelable:true});if(!window.dispatchEvent(event))return;const index=window.history.state?.idx;if(typeof index==='number'&&index>0)navigate(-1);else navigate('/customer/dashboard',{replace:true});}}><ArrowLeft size={19}/></button></div>;
}
