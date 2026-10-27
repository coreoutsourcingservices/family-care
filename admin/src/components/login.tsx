'use client';
import {useEffect, useState, FormEvent} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {HeartPulse, ArrowRight, ShieldCheck, Activity, Users, Eye, EyeOff, ArrowLeft, LoaderCircle, Mail, LockKeyhole} from 'lucide-react';
import {api,post,refreshSession} from '@/lib/api';
import {Role, apiRole, rolePath} from '@/lib/types';
type Result = {challenge_token?:string;requires_password_change?:boolean;user?:{role:string}};
export default function Login({role,registration=false}:{role:Role;registration?:boolean}) {
 const router=useRouter(); const superadmin=role==='SUPERADMIN';
 const [step,setStep]=useState<'login'|'otp'|'password'|'register'|'done'>(registration?'register':'login'); const [identifier,setIdentifier]=useState(''); const [password,setPassword]=useState('');
 const [fullName,setFullName]=useState(''); const [mobile,setMobile]=useState('');
 const [challenge,setChallenge]=useState(''); const [otp,setOtp]=useState(''); const [nextPassword,setNextPassword]=useState(''); const [confirm,setConfirm]=useState('');
 const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [notice,setNotice]=useState(''); const [show,setShow]=useState(false); const [cooldown,setCooldown]=useState(0);
 useEffect(()=>{if(!cooldown)return;const id=setTimeout(()=>setCooldown(c=>c-1),1000);return()=>clearTimeout(id);},[cooldown]);
 useEffect(()=>{if(new URLSearchParams(window.location.search).get('session')!=='expired')return;let active=true;setBusy(true);refreshSession().then(()=>api<{user:{role:string}}>(`${apiRole(role)}/me`,{},false)).then(result=>{if(active&&result.user.role===role){router.replace(`${rolePath(role)}/dashboard`);router.refresh();}}).catch(()=>{if(active)setNotice('Your session has ended. Please sign in again.');}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[role,router]);
 async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError('');setNotice('');try{
  let result:Result;
  if(step==='register') result=await post<Result>('admin/register',{full_name:fullName,email:identifier,mobile_number:mobile,password,confirm_password:confirm});
  else if(step==='login') result=await post<Result>(`${apiRole(role)}/login`,{email:identifier,password});
  else if(step==='otp') result=await post<Result>('admin/verify-email',{challenge_token:challenge,otp});
  else result=await post<Result>('auth/initial-password',{challenge_token:challenge,current_password:password,new_password:nextPassword,confirm_password:confirm});
  if(result.requires_password_change){setChallenge(result.challenge_token!);setStep('password');}
  else if(step==='register'&&result.challenge_token){setChallenge(result.challenge_token);setPassword('');setConfirm('');setStep('otp');setCooldown(60);setNotice('Check your inbox for the 6-digit registration code.');}
  else if(step==='otp'&&result.user){setStep('done');setNotice('Your email is verified. Your registration is waiting for superadmin approval.');}
  else if(result.user?.role===role){setPassword('');router.replace(`${rolePath(role)}/dashboard`);router.refresh();}
  else throw new Error('This account does not have access to this portal.');
 }catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function resend(){setBusy(true);setError('');try{const r=await post<Result>('admin/resend-otp',{challenge_token:challenge});setChallenge(r.challenge_token!);setCooldown(60);setNotice('A new registration code was sent. Use the latest email.');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <main className="login-page">
 <section className="login-story"><Link href="/" className="brand light"><span className="brand-symbol"><HeartPulse size={25}/></span>familycare<span className="brand-dot">.</span></Link>
 <div className="story-body"><span className="story-tag"><span/> CONNECTED CARE, SIMPLIFIED</span><h1>Better care starts<br/>with a better<br/><em>connection.</em></h1><p>A thoughtful workspace for the people<br className="desktop"/> who keep your care network moving.</p>
 <div className="care-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="central-heart"><HeartPulse size={52} strokeWidth={1.5}/></div><div className="care-node node-top"><ShieldCheck size={20}/><span>Trusted professionals</span></div><div className="care-node node-bottom"><Users size={20}/><span>People at the center</span></div><div className="pulse-line"><Activity size={30}/><span>One connected care network</span></div></div></div>
 <div className="story-footer"><ShieldCheck size={17}/><span>Secure access. Meaningful care.</span><span className="story-year">FAMILYCARE</span></div></section>
 <section className="login-content"><div className="portal-label"><span className="tiny-dot"/>{superadmin?'SUPERADMIN':'ADMIN'} PORTAL</div><div className="login-form-wrap">
 {step!=='login'&&step!=='done'&&<button className="text-button back" onClick={()=>{setStep('login');setError('');setNotice('');setOtp('');}}><ArrowLeft size={16}/> Back to sign in</button>}
 <div className="login-icon">{step==='otp'?<Mail/>:step==='password'?<LockKeyhole/>:<ShieldCheck/>}</div>
 <p className="eyebrow">{step==='register'?'JOIN YOUR CARE NETWORK':step==='done'?'REGISTRATION COMPLETE':step==='login'?'YOUR CARE WORKSPACE':step==='otp'?'VERIFY YOUR EMAIL':'KEEP YOUR ACCOUNT SECURE'}</p>
 <h2>{step==='register'?'Create an admin account.':step==='done'?'Registration received.':step==='login'?'Welcome back.':step==='otp'?'Check your email.':'Set a new password.'}</h2><p className="login-subtitle">{step==='register'?'Register, verify your email, then wait for account approval.':step==='done'?'You can sign in after a superadmin approves your account.':step==='login'?`Sign in to manage your ${superadmin?'administration':'care'} network.`:step==='otp'?`Enter the registration code sent to ${identifier}.`:'Replace your initial password before continuing.'}</p>
 {step!=='done'&&<form onSubmit={submit}>
 {step==='register'&&<><label htmlFor="full-name">Full name</label><input id="full-name" autoComplete="name" value={fullName} maxLength={120} onChange={e=>setFullName(e.target.value)} required/><label htmlFor="mobile">Mobile number</label><input id="mobile" type="tel" autoComplete="tel" placeholder="+919876543210" pattern="[+]?[1-9][0-9]{7,14}" value={mobile} onChange={e=>setMobile(e.target.value)} required/></>}
 {(step==='login'||step==='register')&&<><label htmlFor="identifier">Email address</label><input id="identifier" type="email" autoComplete="username" placeholder="you@yourclinic.com" value={identifier} onChange={e=>setIdentifier(e.target.value)} required/><label htmlFor="password">Password</label><div className="password-field"><input id="password" type={show?'text':'password'} autoComplete={step==='register'?'new-password':'current-password'} minLength={step==='register'?8:1} maxLength={128} placeholder="Enter your password" value={password} onChange={e=>setPassword(e.target.value)} required/><button type="button" aria-label={show?'Hide password':'Show password'} onClick={()=>setShow(!show)}>{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></>}
 {step==='register'&&<><label htmlFor="register-confirm">Confirm password</label><input id="register-confirm" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={confirm} onChange={e=>setConfirm(e.target.value)} required/></>}
 {step==='otp'&&<><label htmlFor="otp">Verification code</label><input id="otp" className="otp-input" autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} placeholder="000000" value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,''))} required/><p className="field-note">Codes expire after 5 minutes. Check spam if needed.</p></>}
 {step==='password'&&<><label htmlFor="new-password">New password</label><input id="new-password" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={nextPassword} onChange={e=>setNextPassword(e.target.value)} required/><label htmlFor="confirm-password">Confirm new password</label><input id="confirm-password" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={confirm} onChange={e=>setConfirm(e.target.value)} required/></>}
 {error&&<div className="alert error" role="alert">{error}</div>}{notice&&<div className="alert success" role="status">{notice}</div>}
 <button className="primary login-submit" disabled={busy}>{busy?<LoaderCircle className="spin" size={18}/>:<>{step==='register'?'Register & send OTP':step==='login'?'Sign in':step==='otp'?'Verify email':'Update password & continue'}<ArrowRight size={18}/></>}</button>
 {step==='otp'&&<button className="text-button resend" type="button" disabled={busy||cooldown>0} onClick={resend}>{cooldown?`Resend code in ${cooldown}s`:'Resend verification code'}</button>}
 </form>}{step==='done'&&<><div className="alert success" role="status">{notice}</div><Link href="/" className="primary button">Back to sign in <ArrowRight size={17}/></Link></>}<div className="login-security"><LockKeyhole size={14}/> Your workspace is protected with secure authentication.</div>{!superadmin&&<p className="switch-portal">{registration?'Already have an account?':'New to Familycare?'} <Link href={registration?'/':'/register'}>{registration?'Admin sign in':'Register as admin'} <ArrowRight size={13}/></Link></p>}
 </div><footer className="login-footer">&copy; {new Date().getFullYear()} Familycare <span>Built around better care.</span></footer></section></main>;
}
