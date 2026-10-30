import { useState } from 'react';
import { Check, Copy, Link2 } from 'lucide-react';
import { getDoctorWorkspace } from '../onboarding/setupSession';

export default function DoctorReferralId() {
  const account = getDoctorWorkspace();
  const referral = account?.user.referral_id;
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const approved = account?.user.approval_status === 'APPROVED';
  return <section id="doctor-referral-id" className="doctor-referral-banner" aria-label="Your doctor referral ID"><span className="doctor-referral-symbol"><Link2 size={21} /></span><div><small>Your referral ID</small><strong>{referral || 'Not available yet'}</strong><p>{approved ? 'Share this ID with families so they can connect to your practice.' : 'Families can use this ID after your doctor account is approved.'}</p></div><button type="button" className="dw-secondary" disabled={!referral} aria-label="Copy referral ID" onClick={async () => {
    if (!referral) return;
    setError(''); setCopied(false);
    try { await navigator.clipboard.writeText(referral); setCopied(true); }
    catch { setError('Select the referral ID above and copy it manually.'); }
  }}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? 'Copied!' : 'Copy ID'}</button>{copied && <span className="sr-only" role="status">Referral ID copied.</span>}{error && <p className="doctor-referral-copy-error" role="status">{error}</p>}</section>;
}
