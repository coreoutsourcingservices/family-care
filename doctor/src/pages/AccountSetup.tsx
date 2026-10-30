import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, CircleCheck, Clock3, ClipboardList, Mail, MapPin, Phone, ShieldCheck, Stethoscope, UserRound } from 'lucide-react';
import { authApi, ApiError } from '../../../app/src/lib/authApi';
import { medicalCouncils } from '../data/medicalCouncils';
import { clearDoctorSetup, getDoctorSetup, markDoctorPending } from '../onboarding/setupSession';
import SetupImageField from '../components/SetupImageField';
import { uploadSetupImage } from '../onboarding/uploadImage';
import type { ImageKind } from '../onboarding/uploadImage';
import DoctorWorkspaceLayout from '../components/DoctorWorkspaceLayout';
import DoctorProfileSummary from '../components/DoctorProfileSummary';
import './account-setup.css';

export default function AccountSetup() {
  const navigate = useNavigate();
  const [session] = useState(getDoctorSetup);
  const source = session?.doctor;
  const initialCouncil = medicalCouncils.find(council => council.toUpperCase() === source?.registering_council?.toUpperCase()) ?? source?.registering_council ?? '';
  const [fields, setFields] = useState({
    qualification: source?.qualification ?? '',
    medical_registration_number: source?.medical_registration_number ?? '',
    registering_council: initialCouncil,
    specialization: source?.specialization ?? '', nmr_id: source?.nmr_id ?? '',
    address: source?.address ?? '', clinic_address: source?.clinic_address ?? '',
    years_of_experience: source?.years_of_experience?.toString() ?? '',
  });
  const [otherCouncil, setOtherCouncil] = useState(!!initialCouncil && !medicalCouncils.includes(initialCouncil));
  const [images, setImages] = useState<Partial<Record<ImageKind, File>>>({});
  const [savedImages, setSavedImages] = useState(source?.images ?? {});
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [expired, setExpired] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const inFlight = useRef(false);
  const statusHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!session || submitted) return;
    const timer = window.setTimeout(() => { clearDoctorSetup(); setExpired(true); }, Math.max(0, session.expiresAt - Date.now()));
    return () => window.clearTimeout(timer);
  }, [session, submitted]);
  useEffect(() => { if (submitted || expired) statusHeading.current?.focus(); }, [submitted, expired]);

  function update(name: keyof typeof fields, value: string) {
    setFields(previous => ({ ...previous, [name]: value })); setError('');
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !session || expired) return;
    if (session.expiresAt <= Date.now()) { clearDoctorSetup(); setExpired(true); return; }
    if (fields.qualification.trim().length < 2 || fields.registering_council.trim().length < 2) { setError('Enter your qualification and full registering council name.'); return; }
    if (fields.address.trim().length < 5 || fields.clinic_address.trim().length < 5) { setError('Enter a complete personal and clinic address (at least 5 characters each).'); return; }
    const years = Number(fields.years_of_experience);
    if (fields.years_of_experience === '' || !Number.isInteger(years) || years < 0 || years > 80) { setError('Enter years of experience as a whole number between 0 and 80.'); return; }
    inFlight.current = true; setBusy(true); setError('');
    try {
      let uploadedImages = savedImages;
      for (const kind of ['profile_photo', 'degree_photo'] as const) {
        const file = images[kind];
        if (!file) continue;
        setUploading(true);
        const uploaded = await uploadSetupImage(session.token, kind, file);
        uploadedImages = uploaded.images ?? {};
        setSavedImages(uploadedImages);
        setImages(previous => ({ ...previous, [kind]: undefined }));
      }
      setUploading(false);
      const result = await authApi('/doctors/setup-profile', {
        setup_token: session.token,
        qualification: fields.qualification.trim(),
        medical_registration_number: fields.medical_registration_number.trim(),
        registering_council: fields.registering_council.trim(),
        address: fields.address.trim(), clinic_address: fields.clinic_address.trim(),
        years_of_experience: years,
        specialization: fields.specialization.trim() || null, nmr_id: fields.nmr_id.trim() || null,
      }, 'POST', false);
      if (result.user?.role !== 'DOCTOR' || result.user.approval_status !== 'PENDING_APPROVAL') {
        throw new Error('The server did not confirm submission for approval. Sign in to check your current status.');
      }
      markDoctorPending({ ...fields, years_of_experience: years, images: uploadedImages }); setSubmitted(true); navigate('/doctor/dashboard', { replace: true });
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) { clearDoctorSetup(); setExpired(true); }
      else setError(failure instanceof Error ? failure.message : 'Could not submit your account setup. Please try again.');
    } finally { inFlight.current = false; setBusy(false); setUploading(false); }
  }

  return <DoctorWorkspaceLayout><div className="doctor-setup-page"><div className="doctor-setup-shell">
    <div className="doctor-setup-top"><Link to="/doctor/dashboard" className="doctor-setup-back"><ArrowLeft size={15} />Back to Dashboard</Link></div>
    {!session || expired ? <section className="doctor-setup-status"><span className="doctor-setup-status-icon"><ShieldCheck size={32} /></span><h1 tabIndex={-1} ref={statusHeading}>{expired ? 'Your setup session has expired.' : 'Sign in to continue account setup.'}</h1><p>Use your doctor email and password to get a fresh setup session. Your submitted account details will be restored by the server.</p><Link className="button primary" to="/doctor/login">Go to Doctor Login <ArrowRight size={17} /></Link></section> : submitted ? <section className="doctor-setup-status"><span className="doctor-setup-status-icon"><Clock3 size={32} /></span><span className="doctor-setup-kicker">SUBMITTED FOR ADMIN REVIEW</span><h1 tabIndex={-1} ref={statusHeading}>Your profile is under review.</h1><p>Thank you, {session.user.full_name}. Your account setup has been submitted for approval. Dashboard access will be available after an admin approves your doctor account.</p><div className="doctor-setup-review-flow"><span><Check />Email verified</span><span><Check />Account setup submitted</span><span><Clock3 />Admin approval pending</span></div><Link className="button primary" to="/doctor/login">Back to Doctor Login <ArrowRight size={17} /></Link></section> : <>
      <div className="doctor-setup-intro"><span className="doctor-setup-kicker">DOCTOR ACCOUNT SETUP</span><h1>A little more about<br /><span>the care you provide.</span></h1><p>Review your details and complete your profile for admin review.</p></div>
      <ol className="doctor-setup-progress" aria-label="Doctor onboarding progress">{['Signup & email verification', 'Account setup', 'Admin review'].map((label, index) => <li key={label} aria-current={index === 1 ? 'step' : undefined}><span>{index === 0 ? <Check size={16} /> : index + 1}</span>{label}</li>)}</ol>
      <div className="doctor-setup-layout"><DoctorProfileSummary profile={fields} photo={savedImages.profile_photo?.url} hasDegree={!!savedImages.degree_photo || !!images.degree_photo} />
      <form onSubmit={submit} className="doctor-setup-form" aria-busy={busy}>
        {session.rejectionReason && <div className="doctor-setup-rejection" role="status"><strong>Changes requested by the reviewer</strong><p>{session.rejectionReason}</p><small>Update the details below and submit your profile again.</small></div>}
        <section className="doctor-setup-section"><div className="doctor-setup-section-heading"><span><UserRound /></span><div><h2>Your verified account</h2><p>These details come from your account and cannot be edited here.</p></div><CircleCheck className="doctor-verified-icon" size={20} /></div><div className="doctor-setup-verified-grid"><label><UserRound size={15} />Full Name<input name="verified_name" value={session.user.full_name} readOnly /></label><label><Mail size={15} />Email Address<input name="verified_email" value={session.user.email ?? ''} readOnly /></label><label><Phone size={15} />Mobile Number<input name="verified_phone" value={session.user.phone_number ?? ''} readOnly /></label></div></section>
        <fieldset disabled={busy}><section className="doctor-setup-section"><div className="doctor-setup-section-heading"><span><Stethoscope /></span><div><h2>Professional details</h2><p>Review your registration details and complete your qualifications.</p></div></div><div className="doctor-setup-fields">
          <label>Medical Registration Number<input name="medical_registration_number" value={fields.medical_registration_number} onChange={event => update('medical_registration_number', event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9\/ ._\-]{1,99}" maxLength={100} placeholder="Your medical registration number" /></label>
          <label>Registering Council<select name="registering_council" required value={otherCouncil ? '__other__' : fields.registering_council} onChange={event => { setOtherCouncil(event.target.value === '__other__'); update('registering_council', event.target.value === '__other__' ? '' : event.target.value); }}><option value="" disabled>Select your medical council</option>{medicalCouncils.map(council => <option key={council} value={council}>{council}</option>)}<option value="__other__">Other / Council not listed</option></select></label>
          {otherCouncil && <label className="doctor-setup-wide">Other Council Name<input name="other_council" value={fields.registering_council} onChange={event => update('registering_council', event.target.value)} required minLength={2} maxLength={200} placeholder="Full council name" /></label>}
          <label>Degree / Qualification<input name="qualification" value={fields.qualification} onChange={event => update('qualification', event.target.value)} required minLength={2} maxLength={200} placeholder="e.g. MBBS, MD" /></label>
          <label>Specialization <small>Optional</small><input name="specialization" value={fields.specialization} onChange={event => update('specialization', event.target.value)} maxLength={200} placeholder="e.g. Pediatrics" /></label>
          <label>NMR ID <small>Optional</small><input name="nmr_id" value={fields.nmr_id} onChange={event => update('nmr_id', event.target.value)} maxLength={100} placeholder="National Medical Register ID" /></label>
          <label>Years of Experience<input name="years_of_experience" type="number" inputMode="numeric" value={fields.years_of_experience} onChange={event => update('years_of_experience', event.target.value)} required min={0} max={80} step={1} placeholder="0 for newly qualified doctors" /></label>
        </div></section><section className="doctor-setup-section"><div className="doctor-setup-section-heading"><span><MapPin /></span><div><h2>Where you practise</h2><p>Add your personal and clinic address for professional review.</p></div></div><div className="doctor-setup-fields"><label className="doctor-setup-wide">Personal Address<textarea name="address" value={fields.address} onChange={event => update('address', event.target.value)} autoComplete="street-address" required minLength={5} maxLength={1000} rows={3} placeholder="Street, area, city, state and PIN code" /></label><label className="doctor-setup-wide">Clinic / Hospital Address<textarea name="clinic_address" value={fields.clinic_address} onChange={event => update('clinic_address', event.target.value)} required minLength={5} maxLength={1000} rows={3} placeholder="Clinic or hospital name and complete practice address" /></label></div></section>
        <section className="doctor-setup-section"><div className="doctor-setup-section-heading"><span><UserRound /></span><div><h2>Profile &amp; degree photos</h2><p>Add your doctor photo and a clear image of your degree for the reviewer.</p></div></div><div className="doctor-setup-fields">{(['profile_photo', 'degree_photo'] as const).map(kind => <SetupImageField key={kind} kind={kind} label={kind === 'profile_photo' ? 'Doctor Profile Photo' : 'Degree Photo'} file={images[kind]} savedUrl={savedImages[kind]?.url} onChange={(name, file) => { setImages(previous => ({ ...previous, [name]: file })); setError(''); }} />)}</div><p className="doctor-setup-image-note">Images are saved privately. Uploading a photo does not submit your profile for approval.</p></section>
        {error && <p className="doctor-setup-error" role="alert">{error}</p>}<div className="doctor-setup-submit"><p><ClipboardList size={17} />Your details will be sent to an admin for review.</p><button className="button primary" type="submit">{busy ? uploading ? 'Uploading photos...' : 'Submitting...' : 'Proceed for Approval'}<ArrowRight size={17} /></button></div></fieldset>
      </form></div>
    </>}
  </div></div></DoctorWorkspaceLayout>;
}
