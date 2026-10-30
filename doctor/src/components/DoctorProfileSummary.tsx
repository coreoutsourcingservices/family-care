import { Check, ClipboardList, FileText, MapPin, ShieldCheck, UserRound } from 'lucide-react';
import { getDoctorWorkspace } from '../onboarding/setupSession';

type Profile = { qualification?: string | null; medical_registration_number?: string | null; registering_council?: string | null; specialization?: string | null; address?: string | null; clinic_address?: string | null; years_of_experience?: string | number | null };
export default function DoctorProfileSummary({ profile, photo, hasDegree = false }: { profile?: Profile; photo?: string; hasDegree?: boolean }) {
  const account = getDoctorWorkspace();
  const pending = ['PENDING_APPROVAL', 'APPROVED'].includes(account?.user.approval_status ?? '');
  const professional = !!(profile?.qualification?.trim() && profile.medical_registration_number?.trim() && profile.registering_council?.trim());
  const practice = !!(profile?.address?.trim() && profile.clinic_address?.trim() && profile.years_of_experience !== null && profile.years_of_experience !== undefined && profile.years_of_experience !== '');
  const progress = Math.round(([true, professional, practice, pending].filter(Boolean).length / 4) * 100);
  const steps = [['Personal Details', true, UserRound], ['Professional Details', professional, ShieldCheck], ['Practice Address', practice, MapPin], ['Profile Photo · optional', !!photo, UserRound], ['Degree Photo · optional', hasDegree, FileText], ['Submit for Approval', pending, ClipboardList]] as const;
  return <aside className="doctor-profile-summary"><div className="doctor-profile-avatar">{photo ? <img src={photo} alt="Your doctor profile" /> : <UserRound size={65} strokeWidth={1.3} />}</div><h2>{account?.user.full_name ?? 'Doctor'}</h2><p>{profile?.specialization || profile?.qualification || 'Your professional profile'}</p>{profile?.registering_council && <small>{profile.registering_council}</small>}<div className="doctor-profile-progress"><div role="progressbar" aria-label="Required profile steps complete" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><span style={{ width: `${progress}%` }} /></div><small>Required steps {progress}% complete</small></div><ul>{steps.map(([label, done, Icon]) => <li key={label}><span className={done ? 'done' : ''}>{done ? <Check size={13} /> : <Icon size={14} />}</span>{label}</li>)}</ul></aside>;
}
