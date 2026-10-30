import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Bell, CalendarDays, Check, ClipboardList, Eye, EyeOff, Heart, LockKeyhole, Mail, Pencil, ShieldCheck, Stethoscope, UserRound, Users } from 'lucide-react';
import { Logo } from '../../components/Website';
import './auth.css';
import DoctorRegistrationFields, { DoctorSignupSteps } from '../../../../doctor/src/components/RegistrationFields';
import type { DoctorAuthOutcome } from '../../../../doctor/src/onboarding/types';
import { authApi, ApiError, type AuthResponse } from '../../lib/authApi';

type Role = 'customer' | 'doctor';
type Step = 'details' | 'professional' | 'otp' | 'complete';
type Fields = { name: string; phone: string; email: string; password: string; registration: string; council: string; qualification: string };
const initialFields: Fields = { name: '', phone: '', email: '', password: '', registration: '', council: '', qualification: '' };

function RoleSwitch({ role, mode }: { role: Role; mode: 'signup' | 'login' }) {
  return <div className="auth-role-switch" aria-label="Account type"><Link to={`/customer/${mode}`} aria-current={role === 'customer' ? 'page' : undefined}>Customer / Parent</Link><Link to={`/doctor/${mode}`} aria-current={role === 'doctor' ? 'page' : undefined}>Doctor</Link></div>;
}

export default function AuthPage({ role, mode, onDoctorResult }: { role: Role; mode: 'signup' | 'login'; onDoctorResult?: (data: AuthResponse) => DoctorAuthOutcome }) {
  const navigate = useNavigate();
  const doctor = role === 'doctor';
  const signup = mode === 'signup';
  const [fields, setFields] = useState<Fields>(() => ({ ...initialFields, email: signup ? '' : localStorage.getItem('familycare_remember_email') ?? '' }));
  const [step, setStep] = useState<Step>('details');

  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState<string[]>(Array(6).fill(''));
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [forgot, setForgot] = useState(false);
  const [remember, setRemember] = useState(() => !!localStorage.getItem('familycare_remember_email'));
  const [busy, setBusy] = useState(false);
  const [challenge, setChallenge] = useState('');
  const [completion, setCompletion] = useState<'session' | 'approval'>('session');
  const [resumeVerification, setResumeVerification] = useState(false);
  const requestInFlight = useRef(false);
  const endpoint = doctor ? '/doctors' : '/patients';
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);
  const headingRef = useRef<HTMLHeadingElement>(null);


  useEffect(() => {
    if (step !== 'otp') return;
    otpRefs.current[0]?.focus();
    const interval = window.setInterval(() => setCooldown(previous => Math.max(0, previous - 1)), 1000);
    return () => window.clearInterval(interval);
  }, [step]);
  useEffect(() => { if (step === 'professional' || step === 'complete') headingRef.current?.focus(); }, [step]);

  function update(name: keyof Fields, value: string) {
    setFields(previous => ({ ...previous, [name]: value }));
    setError(''); setMessage('');
  }
  function startChallenge(data: AuthResponse) {
    if (!data.challenge_token) throw new Error('Email verification could not start. Please request a fresh verification code.');
    setChallenge(data.challenge_token);
    setOtp(Array(6).fill('')); setCooldown(data.resend_after ?? 60); setStep('otp');
    setMessage(data.email_status === 'sent' ? 'OTP sent to your email. Please check your inbox and spam folder.' : 'Your email OTP is queued. Please check your inbox and spam folder.');
  }
  function complete(kind: 'session' | 'approval') {
    if (kind === 'session' && !signup) {
      if (remember) localStorage.setItem('familycare_remember_email', fields.email.trim());
      else localStorage.removeItem('familycare_remember_email');
    }
    setCompletion(kind); setStep('complete'); setChallenge('');
    setFields(previous => ({ ...previous, password: '' }));
    if (kind === 'session') navigate(doctor ? '/doctor/dashboard' : '/customer/dashboard', { replace: true });
  }
  function handleDoctorResponse(data: AuthResponse) {
    if (!onDoctorResult) throw new Error('Doctor authentication is unavailable. Please reload this page.');
    const outcome = onDoctorResult(data);
    if (outcome === 'setup') {
      setFields(previous => ({ ...previous, password: '' })); setChallenge(''); return true;
    }
    if (outcome === 'approval') { complete('approval'); return true; }
    return false;
  }
  async function run(action: () => Promise<void>) {
    if (requestInFlight.current) return;
    requestInFlight.current = true; setBusy(true); setError(''); setMessage('');
    try { await action(); }
    catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Something went wrong. Please try again.');
      if (failure instanceof ApiError && failure.code === 'account_restricted' && !signup) setResumeVerification(true);
    }
    finally { requestInFlight.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run(async () => {
      if (step === 'otp') {
        const code = otp.join('');
        if (!/^\d{6}$/.test(code)) throw new Error('Enter the 6-digit code from your email.');
        const data = await authApi(`${endpoint}/verify-email`, { challenge_token: challenge, otp: code });
        if (doctor) {
          if (!handleDoctorResponse(data)) throw new Error('Please sign in to continue doctor account setup.');
        }
        else {
          if (!data.csrf_token || !data.user) throw new Error('The server did not establish a session. Please sign in again.');
          complete('session');
        }
        return;
      }
      if (!signup) {
        if (forgot) { const data = await authApi('/auth/forgot-password', { email: fields.email.trim() }); setMessage(data.message ?? 'If an eligible account exists, reset instructions are queued for your email.'); return; }
        const data = await authApi(`${endpoint}/login`, { email: fields.email.trim(), password: fields.password });
        if (doctor && handleDoctorResponse(data)) return;
        if (!data.csrf_token || !data.user) throw new Error('Sign-in did not return a session. Restart the backend and try again.');
        complete('session');
        return;
      }
      if (step === 'details' && doctor) { setStep('professional'); return; }
      if (challenge) { startChallenge(await authApi('/auth/request-email-verification', { email: fields.email.trim(), password: fields.password })); return; }
      const data = await authApi(`${endpoint}/register`, {
        full_name: fields.name.trim(), email: fields.email.trim(), mobile_number: `+91${fields.phone}`,
        password: fields.password, confirm_password: fields.password,
        ...(doctor ? { medical_registration_number: fields.registration.trim(), registering_council: fields.council.trim(), qualification: fields.qualification.trim() } : {}),
      });
      startChallenge(data);
    });
  }
  async function resend() {
    await run(async () => { startChallenge(await authApi('/auth/resend-otp', { challenge_token: challenge })); });
  }
  async function restartVerification() {
    await run(async () => { startChallenge(await authApi('/auth/request-email-verification', { email: fields.email.trim(), password: fields.password })); setResumeVerification(false); });
  }
  function enterOtp(value: string, index: number) {
    const digits = value.replace(/\D/g, '').slice(0, 6 - index);
    setError('');
    setOtp(previous => {
      const next = [...previous];
      if (!digits) next[index] = '';
      else digits.split('').forEach((digit, offset) => { next[index + offset] = digit; });
      return next;
    });
    if (digits) otpRefs.current[Math.min(index + digits.length, 5)]?.focus();
  }
  function editDetails() { setStep('details'); setOtp(Array(6).fill('')); setError(''); setMessage(''); setResumeVerification(false); }

  const sidebarItems = doctor
    ? [[Users, 'Connect with families'], [ClipboardList, 'Organize patient records'], [Stethoscope, 'Build your professional profile'], [CalendarDays, 'Manage consultation requests']] as const
    : [[ShieldCheck, 'Track vaccinations & milestones'], [ClipboardList, 'Manage health records'], [Bell, 'Keep reminders in view'], [Users, 'Care for your whole family']] as const;
  return <div className={`auth-page ${doctor ? 'auth-doctor' : 'auth-customer'} ${!signup ? 'auth-login' : ''}`}>
    <div className="auth-frame">
      <aside className="auth-story"><Logo /><div className="auth-story-copy"><span className="auth-kicker">{doctor ? 'CARE STARTS WITH YOU' : 'ONE FAMILY. EVERY STAGE.'}</span><h2>{doctor ? <>Join Our <span>Doctor Network</span></> : signup ? <>Create Your<br /><span>Family Account</span></> : <>Better Health.<br /><span>Happier Families.</span></>}</h2><p>{doctor ? 'A dedicated space for doctors to connect with families and bring care into focus.' : 'Your child’s, women’s and adult health records — together in one thoughtful place.'}</p><ul>{sidebarItems.map(([Icon, text]) => <li key={text}><span><Icon size={16} /></span>{text}</li>)}</ul></div><div className="auth-story-image"><img src={doctor ? '/images/doctor-auth.png' : '/images/family.png'} alt={doctor ? 'A friendly doctor in a white coat' : 'Parents embracing their smiling daughter'} /><span className="auth-handwritten">{doctor ? <>Your expertise.<br />Healthier<br />tomorrows.</> : <>Healthy families.<br />Brighter<br />tomorrows.</>}<Heart size={21} /></span><span className="auth-leaf auth-leaf-one" /><span className="auth-leaf auth-leaf-two" /></div></aside>
      <section className="auth-panel" aria-label={`${doctor ? 'Doctor' : 'Customer'} ${signup ? 'registration' : 'login'}`}>
        <Link to="/" className="auth-back"><ArrowLeft size={14} />Back to Home</Link>
        <div className="auth-form-wrap">
          {step !== 'complete' && <><div className="auth-heading"><span className="auth-form-kicker">{signup ? 'YOUR FAMILYCARE+ JOURNEY' : 'WELCOME BACK'}</span><h1 ref={headingRef} tabIndex={-1}>{step === 'otp' ? 'Verify OTP' : step === 'professional' ? 'Professional Information' : !signup ? forgot ? 'Reset Password' : `${doctor ? 'Doctor' : 'Customer'} Login` : doctor ? 'Doctor Registration' : 'Create an Account'}</h1><p>{step === 'otp' ? <>Enter the code sent to your email.<strong className="otp-number">{fields.email}</strong></> : step === 'professional' ? 'Add your registration number, council and qualification here. Complete the rest of your account setup after email verification.' : signup ? doctor ? 'Join FamilyCare+ through a separate professional account.' : 'Join FamilyCare+ to begin your family’s health journey.' : forgot ? 'Enter the email associated with your account.' : 'Choose your account type and enter your details.'}</p></div><RoleSwitch role={role} mode={mode} />{doctor && signup && <DoctorSignupSteps step={step} />}</>}
          <form onSubmit={submit} className="auth-form" aria-busy={busy}><fieldset className="auth-request-fields" disabled={busy}>
            {step === 'complete' ? <div className="auth-complete"><span className="auth-success-icon"><Check size={32} /></span><h1 ref={headingRef} tabIndex={-1}>{completion === 'approval' ? 'Your profile is under review.' : 'You are signed in.'}</h1><p>{completion === 'approval' ? 'Your doctor registration is awaiting approval. You can sign in after your account is approved.' : 'Your account session is active.'}</p>{completion !== 'session' && <Link to={`/${role}/login`} onClick={() => { setStep('details'); setForgot(false); }} className="button auth-submit">Go to {doctor ? 'Doctor' : 'Customer'} Login <ArrowRight size={17} /></Link>}{completion === 'session' && <button type="button" className="button auth-submit" disabled={busy} onClick={() => run(async () => { await authApi('/auth/logout'); setStep('details'); setForgot(false); })}>{busy ? 'Signing out...' : 'Sign out'}</button>}{error && <p className="auth-error" role="alert">{error}</p>}<Link to="/" className="auth-text-link">Back to Home</Link></div> : <>
              {signup && step === 'details' && <><label className="auth-field"><UserRound /><span>Full Name<input name="name" autoComplete="name" placeholder="Enter your full name" value={fields.name} onChange={event => update('name', event.target.value)} required minLength={2} maxLength={100} /></span></label><div className="auth-phone"><span className="country-code" aria-label="India country code">🇮🇳 <strong>+91</strong></span><label className="auth-field"><span>Mobile Number<input name="phone" type="tel" inputMode="numeric" autoComplete="tel-national" placeholder="Enter your phone number" value={fields.phone} onChange={event => update('phone', event.target.value.replace(/\D/g, '').slice(0, 10))} required pattern="[6-9][0-9]{9}" title="Enter a 10-digit Indian mobile number starting with 6, 7, 8 or 9" /></span></label></div></>}
              {(step === 'details') && <><label className="auth-field"><Mail /><span>Email Address<input name="email" type="email" autoComplete="email" placeholder="Enter your email address" value={fields.email} onChange={event => update('email', event.target.value)} required maxLength={254} /></span></label>{!forgot && <label className="auth-field password-field"><LockKeyhole /><span>Password<input name="password" type={showPassword ? 'text' : 'password'} autoComplete={signup ? 'new-password' : 'current-password'} placeholder={signup ? 'Create a password (8+ characters)' : 'Enter your password'} value={fields.password} onChange={event => update('password', event.target.value)} required minLength={signup ? 8 : undefined} maxLength={128} /></span><button className="auth-password-toggle" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></label>}</>}
              {step === 'professional' && <DoctorRegistrationFields registration={fields.registration} council={fields.council} qualification={fields.qualification} onChange={update} onEditBasic={() => { setStep('details'); setError(''); }} />}
              {step === 'otp' && <><fieldset className="otp-fieldset"><legend>Enter the 6-digit email OTP</legend><div className="otp-inputs">{otp.map((digit, index) => <input key={index} ref={element => { otpRefs.current[index] = element; }} value={digit} aria-label={`OTP digit ${index + 1}`} inputMode="numeric" autoComplete={index === 0 ? 'one-time-code' : 'off'} onChange={event => enterOtp(event.target.value, index)} onPaste={event => { event.preventDefault(); enterOtp(event.clipboardData.getData('text'), index); }} onFocus={event => event.target.select()} onKeyDown={event => { if (event.key === 'Backspace' && !digit && index > 0) otpRefs.current[index - 1]?.focus(); if (event.key === 'ArrowLeft' && index > 0) otpRefs.current[index - 1]?.focus(); if (event.key === 'ArrowRight' && index < 5) otpRefs.current[index + 1]?.focus(); }} maxLength={6} />)}</div></fieldset><div className="otp-resend"><span>Didn't receive OTP?</span><button type="button" disabled={busy || cooldown > 0} onClick={resend}>{cooldown > 0 ? `Resend in ${Math.floor(cooldown / 60)}:${String(cooldown % 60).padStart(2, '0')}` : 'Resend OTP'}</button></div></>}
              {!signup && !forgot && step === 'details' && <div className="auth-login-options"><label title="Remember your email on this device"><input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)} />Remember me</label><button type="button" onClick={() => { setForgot(true); setMessage(''); setError(''); setResumeVerification(false); }}>Forgot Password?</button></div>}
              {error && <p className="auth-error" role="alert">{error}</p>}{message && <p className="auth-message" role="status">{message}</p>}{resumeVerification && step === 'details' && <button type="button" className="auth-text-link" disabled={busy} onClick={restartVerification}>Verify an unverified email</button>}{step === 'otp' && <button type="button" className="auth-text-link" disabled={busy} onClick={restartVerification}>Request a fresh verification challenge</button>}
              <button className="button auth-submit" type="submit" disabled={busy}>{busy ? 'Please wait...' : step === 'otp' ? 'Verify OTP' : step === 'professional' ? 'Continue to OTP' : signup ? doctor ? 'Continue' : 'Send OTP' : forgot ? 'Request Password Reset' : 'Login'}<ArrowRight size={17} /></button>
              {step === 'otp' ? <><div className="auth-divider"><span>or</span></div><button type="button" className="button auth-edit-phone" onClick={editDetails}><Pencil size={15} />{signup ? 'Back to account details' : 'Back to Login'}</button></> : <p className="auth-account-link">{forgot ? <button type="button" onClick={() => { setForgot(false); setMessage(''); }}>Back to Login</button> : <>{signup ? 'Already have an account?' : 'Don’t have an account?'} <Link to={`/${role}/${signup ? 'login' : 'signup'}`}>{signup ? 'Login' : 'Sign Up'}</Link></>}</p>}
            </>}
          </fieldset></form>
          <div className="auth-security"><span><ShieldCheck size={25} /></span><p>Your family. Your permissions.<small>Designed around consent and authorized access.</small></p></div>
          {step !== 'complete' && <p className="auth-preview-label">{signup || step === 'otp' ? 'Email verification codes expire in 5 minutes.' : 'Sign in securely with your email and password.'}</p>}
        </div>
      </section>
    </div>
  </div>;
}
