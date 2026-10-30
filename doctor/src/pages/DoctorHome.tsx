import DashboardCharts from '../components/DashboardCharts';
import { Link } from 'react-router-dom';
import { ArrowRight, Clock3, LockKeyhole, ShieldCheck, Stethoscope } from 'lucide-react';
import { getDoctorWorkspace, getDoctorSetup } from '../onboarding/setupSession';
import DoctorWorkspaceLayout from '../components/DoctorWorkspaceLayout';
import DoctorProfileSummary from '../components/DoctorProfileSummary';
import PracticeDashboard from './PracticeDashboard';
import './doctor-home.css';

export default function DoctorHome() {
  const account = getDoctorWorkspace();
  if (!account) return null;
  if (account.user.approval_status === 'APPROVED') return <PracticeDashboard />;
  const pending = account.user.approval_status === 'PENDING_APPROVAL';
  const rejected = account.user.approval_status === 'REJECTED';
  const canSetup = !!getDoctorSetup();
  return <DoctorWorkspaceLayout><div className="doctor-overview-grid"><DoctorProfileSummary profile={account.doctor} photo={account.doctor?.images?.profile_photo?.url} hasDegree={!!account.doctor?.images?.degree_photo} /><section className="doctor-overview-panels">
    <article className="doctor-home-identity"><div className="doctor-panel-heading"><span><UserIcon /></span><div><h2>Your verified account</h2><p>These details come from your account and cannot be edited here.</p></div><small className="doctor-email-verified"><ShieldCheck size={13} />Email verified</small></div><div className="doctor-identity-grid">{[['Full Name', account.user.full_name], ['Email Address', account.user.email], ['Mobile Number', account.user.phone_number]].map(([label, value]) => <label key={label}>{label}<input value={value ?? ''} readOnly /></label>)}</div></article>
    <article className="doctor-home-profile"><div className="doctor-panel-heading"><span>{pending ? <Clock3 size={22} /> : <Stethoscope size={22} />}</span><div><h2>{pending ? 'Your profile is under review.' : 'Set My Profile'}</h2><p>{pending ? 'Your completed profile has been sent to the admin.' : 'Complete your professional details and send your profile for review.'}</p></div></div><p>{pending ? 'Your clinical workspace will open after admin approval.' : 'Add your practice address, profile photo and degree photo. Nothing is sent for approval until you select Proceed for Approval.'}</p>{rejected && <p role="status">Reviewer feedback: {account.rejectionReason}</p>}{!pending && <Link className="button primary" to={canSetup ? '/doctor/setup-account' : '/doctor/login'}>{canSetup ? 'Set My Profile' : 'Sign in to continue setup'}<ArrowRight size={17} /></Link>}</article>
    <section className="doctor-home-locked"><h2>Your clinical workspace</h2><div>{['Patients', 'Consultations', 'Clinical Records', 'Appointments', 'Prescriptions', 'Reports'].map(title => <article key={title}><LockKeyhole size={18} /><h3>{title}</h3><span>Available after approval</span></article>)}</div></section>
    {!pending && <p className="doctor-home-note"><ShieldCheck size={16} />No approval request has been sent. Submit your completed profile when you are ready.</p>}
  </section></div><DashboardCharts locked /></DoctorWorkspaceLayout>;
}
function UserIcon() { return <Stethoscope size={21} />; }
