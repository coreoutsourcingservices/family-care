import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { authApi } from '../../../app/src/lib/authApi';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { CalendarDays, ClipboardList, FileText, LayoutDashboard, LockKeyhole, LogOut, Search, Settings, Stethoscope, UserRound, Users } from 'lucide-react';
import { Logo } from '../../../app/src/components/Website';
import { clearDoctorWorkspace, getDoctorSetup, getDoctorWorkspace } from '../onboarding/setupSession';
import DoctorReferralId from './DoctorReferralId';
import NotificationCenter from '../notifications/NotificationCenter';
import { disableBrowserPush } from '../notifications/api';
import '../pages/doctor-home.css';

const clinicalMenu = [
  ['Vaccination', CalendarDays, '/doctor/vaccination'],
  ['Patients', Users, '/doctor/patients'], ['Consultations', Stethoscope, '/doctor/consultations'], ['Clinical Records', ClipboardList, '/doctor/clinical-records'],
  ['Appointments', CalendarDays, '/doctor/appointments'], ['Prescriptions', FileText, '/doctor/prescriptions'], ['Reports', ClipboardList, '/doctor/reports'], ['Settings', Settings, '/doctor/settings'],
] as const;

export default function DoctorWorkspaceLayout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [,setProfileRevision]=useState(0);
  useEffect(()=>{const refresh=()=>setProfileRevision(n=>n+1);window.addEventListener('familycare:doctor-updated',refresh);return()=>window.removeEventListener('familycare:doctor-updated',refresh);},[]);
  const account = getDoctorWorkspace();
  const setup = getDoctorSetup();
  const pending = account?.user.approval_status === 'PENDING_APPROVAL';
  const approved = account?.user.approval_status === 'APPROVED';
  const [search, setSearch] = useState('');
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState('');
  const name = account?.user.full_name ?? 'Doctor';
  useEffect(() => {
    const manifest = document.createElement('link'); manifest.rel = 'manifest'; manifest.href = '/doctor.webmanifest'; document.head.append(manifest);
    const icon = document.createElement('link'); icon.rel = 'apple-touch-icon'; icon.href = '/doctor-icon-192.png'; document.head.append(icon);
    return () => { manifest.remove(); icon.remove(); };
  }, []);
  return <div className="doctor-home doctor-workspace"><aside className="doctor-home-sidebar">
    <Logo /><nav aria-label="Doctor workspace">
      <Link className={location.pathname === '/doctor/dashboard' ? 'active' : ''} to="/doctor/dashboard"><LayoutDashboard size={18} />Dashboard</Link>
      {pending ? <button disabled title="Your submitted profile is being reviewed"><UserRound size={18} />Set My Profile<LockKeyhole size={13} /></button> : <Link className={location.pathname === '/doctor/setup-account' ? 'active' : ''} to={approved || setup ? '/doctor/setup-account' : '/doctor/login'}><UserRound size={18} />Set My Profile</Link>}
      {clinicalMenu.map(([label, Icon, path]) => approved ? <Link key={label} className={location.pathname === path ? 'active' : ''} to={path}><Icon size={18} />{label}</Link> : <button key={label} type="button" disabled title="Available after admin approval"><Icon size={18} /><span>{label}</span><LockKeyhole size={12} /></button>)}
    </nav><button className="doctor-sidebar-signout" disabled={signingOut} onClick={async () => { setSigningOut(true); setSignOutError(''); try { await disableBrowserPush().catch(() => {}); if (approved) await authApi('/auth/logout'); clearDoctorWorkspace(); navigate('/doctor/login', { replace: true }); } catch (error) { setSignOutError(error instanceof Error ? error.message : 'Could not sign out'); setSigningOut(false); } }}><LogOut size={17} />Sign out</button>
  </aside><div className="doctor-workspace-main"><header className="doctor-home-header"><div><span className="doctor-welcome">Welcome back,</span><h1>{name} <span aria-hidden="true">👋</span></h1><p>{approved ? 'Your practice. Connected families. Thoughtful care.' : pending ? 'Your profile is with the admin for review.' : 'Complete your profile to start connecting with families.'}</p></div><div className="doctor-header-tools"><form className="doctor-header-search" onSubmit={event => { event.preventDefault(); if (approved) navigate(`/doctor/patients?search=${encodeURIComponent(search)}`); }}><Search size={16} /><input aria-label="Search patients and records" placeholder="Search patients, records..." disabled={!approved} title={approved ? 'Press Enter to search patients' : 'Search is available after approval'} value={search} onChange={event => setSearch(event.target.value)} /></form><NotificationCenter /><div className="doctor-header-account"><span className="doctor-avatar-small">{account?.doctor?.images?.profile_photo?.url?<img src={account.doctor.images.profile_photo.url} alt="Doctor profile" style={{width:"100%",height:"100%",objectFit:"cover",borderRadius:"50%"}}/>:name.charAt(0)}</span><div><strong>{name}</strong><small>{account?.doctor?.specialization || 'Doctor account'}</small></div></div></div></header>
    <div className="doctor-workspace-content"><DoctorReferralId />{signOutError && <p className="dw-error" role="alert">{signOutError}</p>}{children}</div></div></div>;
}
