import { useState } from 'react';
import { Check, ClipboardList, ShieldCheck, Stethoscope } from 'lucide-react';
import { medicalCouncils } from '../data/medicalCouncils';

export function DoctorSignupSteps({ step }: { step: string }) {
  const active = step === 'details' ? 0 : step === 'professional' ? 1 : 2;
  return <ol className="auth-steps" aria-label="Doctor registration steps">{['Basic Details', 'Professional Info', 'Verification'].map((label, index) => <li key={label} aria-current={index === active ? 'step' : undefined} className={index < active ? 'done' : ''}><span>{index < active ? <Check size={15} /> : index + 1}</span><small>{label}</small></li>)}</ol>;
}

export default function RegistrationFields({ registration, council, qualification, onChange, onEditBasic }: {
  registration: string; council: string; qualification: string;
  onChange: (name: 'registration' | 'council' | 'qualification', value: string) => void;
  onEditBasic: () => void;
}) {
  const [other, setOther] = useState(!!council && !medicalCouncils.includes(council));
  return <>
    <label className="auth-field"><ClipboardList /><span>Medical Registration Number<input name="registration" autoComplete="off" placeholder="Enter your medical registration number" value={registration} onChange={event => onChange('registration', event.target.value)} required minLength={3} maxLength={60} /></span></label>
    <label className="auth-field"><Stethoscope /><span>Registering Council<select name="council" required value={other ? '__other__' : council} onChange={event => { setOther(event.target.value === '__other__'); onChange('council', event.target.value === '__other__' ? '' : event.target.value); }}><option value="" disabled>Select your medical council</option>{medicalCouncils.map(name => <option key={name} value={name}>{name}</option>)}<option value="__other__">Other / Council not listed</option></select></span></label>
    {other && <label className="auth-field"><Stethoscope /><span>Other Council Name<input name="otherCouncil" value={council} onChange={event => onChange('council', event.target.value)} required minLength={2} maxLength={200} pattern=".*\S.*" placeholder="Enter the full council name" /></span></label>}
    <label className="auth-field"><ClipboardList /><span>Degree / Qualification<input name="qualification" autoComplete="off" placeholder="e.g. MBBS, MD" value={qualification} onChange={event => onChange('qualification', event.target.value)} required maxLength={200} pattern=".*\S.*" /></span></label>
    <div className="auth-professional-note"><ShieldCheck size={20} /><p>Your registration number will need professional verification before access to patient records.</p></div>
    <button type="button" className="auth-text-link auth-edit-basic" onClick={onEditBasic}>Edit basic details</button>
  </>;
}
