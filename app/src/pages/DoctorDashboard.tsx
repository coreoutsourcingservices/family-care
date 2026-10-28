import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, LogOut, ShieldCheck, Users } from 'lucide-react';
import { Logo } from '../components/Website';
import { ApiError, authApi } from '../lib/authApi';
import { careApi } from '../lib/careApi';
import { fromRemote, loadProfile, downloadReport, type RemoteProfile, type HealthProfile } from '../lib/healthProfiles';
import './customer-dashboard.css';

export default function DoctorDashboard() {
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<HealthProfile[]>([]);
  const [active, setActive] = useState<HealthProfile>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  useEffect(() => {
    let current = true;
    setLoading(true); setError(''); setActive(undefined);
    (async () => {
      const session = await authApi('/doctors/me', undefined, 'GET');
      if (session.user?.role !== 'DOCTOR') { navigate('/doctor/login', { replace: true }); return; }
      const data = await careApi<{ items: RemoteProfile[] }>(`/doctors/care-profiles?page=${page}&per_page=25`);
      if (current) setProfiles(data.items.map(profile => fromRemote(profile, true)));
    })().catch(failure => {
      if (!current) return;
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) navigate('/doctor/login', { replace: true });
      else setError(failure instanceof Error ? failure.message : 'Unable to load referred profiles.');
    }).finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [navigate, page, attempt]);
  async function signOut() {
    setSigningOut(true); setError('');
    try { await authApi('/auth/logout'); navigate('/doctor/login', { replace: true }); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Unable to sign out.'); }
    finally { setSigningOut(false); }
  }
  return <div className="customer-dashboard"><header className="customer-dashboard-header"><Logo /><div className="customer-account-actions"><span>Doctor Portal</span><button type="button" disabled={signingOut} onClick={signOut}><LogOut size={16} />Sign out</button></div></header>
    <div className="doctor-care-dashboard"><span className="member-eyebrow">YOUR REFERRED PROFILES</span><h1>Care, with permission.</h1><p className="doctor-access-note"><ShieldCheck size={17} />Only family profiles referred to you appear here. Other family members are private.</p>
      {error && <div className="customer-dashboard-error" role="alert">{error}<button type="button" className="member-secondary" onClick={() => setAttempt(value => value + 1)}>Try again</button></div>}
      {loading ? <p role="status">Loading referred profiles...</p> : !error && <>
        {profiles.length === 0 ? <div className="doctor-empty"><Users size={35} /><h2>No referred profiles yet</h2><p>Profiles appear when a customer saves your Doctor ID as their referral.</p></div> : <div className="doctor-care-layout"><div className="doctor-profile-list">{profiles.map(profile => <button key={profile.id} type="button" aria-pressed={active?.id === profile.id} onClick={() => { setActive(undefined); setError(''); void loadProfile(profile.id, true).then(setActive).catch(failure => setError(failure instanceof Error ? failure.message : 'Unable to load reports.')); }}><span>{profile.name}</span><small>{profile.module === 'child' ? 'Child Care' : profile.module === 'women' ? 'Women’s Health' : 'Adult Health'}</small></button>)}</div>
          {active ? <section className="doctor-profile-detail"><span className="member-eyebrow">REFERRED PROFILE</span><h2>{active.name}</h2><p>Date of birth: {new Date(`${active.dob}T00:00:00`).toLocaleDateString('en-IN')}</p>{active.guardianContact && <p>Guardian contact: <a href={`tel:${active.guardianContact}`}>{active.guardianContact}</a></p>}
            {active.contacts.length > 0 && <div className="member-saved-contacts"><h4>Emergency contacts</h4><div>{active.contacts.map(contact => <article key={contact.id}><strong>{contact.name}</strong><a href={`tel:${contact.mobile}`}>{contact.mobile}</a></article>)}</div></div>}
            <div className="member-saved-reports"><h4>Health reports</h4>{active.reports.length ? <div>{active.reports.map(report => <button type="button" className="member-report-download" key={report.id} onClick={() => void downloadReport(report).catch(failure => setError(failure instanceof Error ? failure.message : 'Unable to download report.'))}><FileText size={20} /><span>{report.name}</span></button>)}</div> : <p>No reports added.</p>}</div>
          </section> : <section className="doctor-empty"><FileText size={30} /><h2>Choose a profile</h2><p>Select a referred family member to view their details and reports.</p></section>}
        </div>}
        <div className="doctor-pagination">{page > 1 && <button type="button" className="member-secondary" onClick={() => setPage(value => value - 1)}>Previous</button>}{profiles.length === 25 && <button type="button" className="member-secondary" onClick={() => setPage(value => value + 1)}>Next</button>}</div>
      </>}
      <Link to="/" className="member-back-overview">Back to Home</Link>
    </div>
  </div>;
}
