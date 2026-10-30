import ProfilePhotoEditor from '../components/ProfilePhotoEditor';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound, LogOut, ShieldCheck } from 'lucide-react';
import { NotificationPreferences } from '../notifications/NotificationCenter';
import { disableBrowserPush } from '../notifications/api';
import WorkspacePage from '../components/WorkspacePage';
import { authApi } from '../../../app/src/lib/authApi';
import { clearDoctorWorkspace, getDoctorWorkspace } from '../onboarding/setupSession';

export default function Settings() {
  const account = getDoctorWorkspace();
  const navigate = useNavigate();
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function signOutEverywhere() {
    if (busy) return;
    setBusy(true); setError('');
    try { await disableBrowserPush().catch(() => {}); await authApi('/auth/logout-all'); clearDoctorWorkspace(); navigate('/doctor/login', { replace: true }); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not sign out.'); setBusy(false); }
  }
  return <WorkspacePage title="Settings" description="Manage the security of your doctor account."><div className="dw-settings-grid"><ProfilePhotoEditor/><section className="dw-panel"><div className="doctor-panel-heading"><span><ShieldCheck size={21} /></span><div><h2>Account information</h2><p>Verified account details</p></div></div><dl className="dw-detail-list"><div><dt>Name</dt><dd>{account?.user.full_name}</dd></div><div><dt>Email</dt><dd>{account?.user.email}</dd></div><div><dt>Mobile</dt><dd>{account?.user.phone_number}</dd></div><div><dt>Doctor ID</dt><dd>{account?.user.public_id}</dd></div></dl><p className="dw-info">Families control which profiles are connected to you. You can only access the records shared with your doctor account.</p></section>
    <form className="dw-panel dw-form" onSubmit={async event => { event.preventDefault(); if (busy) return; if (passwords.new_password !== passwords.confirm_password) { setError('New passwords must match.'); return; } setBusy(true); setError(''); try { await authApi('/auth/change-password', passwords); await disableBrowserPush().catch(() => {}); clearDoctorWorkspace(); navigate('/doctor/login', { replace: true }); } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not change your password.'); setBusy(false); } }}><div className="doctor-panel-heading"><span><KeyRound size={21} /></span><div><h2>Change password</h2><p>You will sign in again after changing your password.</p></div></div>{([['current_password', 'Current password', 'current-password'], ['new_password', 'New password', 'new-password'], ['confirm_password', 'Confirm new password', 'new-password']] as const).map(([key, label, autocomplete]) => <label key={key}>{label}<input type="password" autoComplete={autocomplete} required minLength={key === 'current_password' ? 1 : 8} maxLength={128} value={passwords[key]} onChange={event => setPasswords(previous => ({ ...previous, [key]: event.target.value }))} /></label>)}<button className="button primary" disabled={busy}>{busy ? 'Please wait...' : 'Update password'}</button></form>
    <section className="dw-panel dw-session-card"><NotificationPreferences /></section><section className="dw-panel dw-session-card"><div><h2>Active sessions</h2><p>Sign out of this account on every device.</p></div><button className="dw-secondary" disabled={busy} onClick={signOutEverywhere}><LogOut size={16} />Sign out everywhere</button></section></div>{error && <p className="dw-error" role="alert">{error}</p>}</WorkspacePage>;
}
