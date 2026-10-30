import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { CalendarDays, FileText, FolderHeart, RefreshCw, Search, Stethoscope, Users } from 'lucide-react';
import DoctorWorkspaceLayout from './DoctorWorkspaceLayout';

export function useWorkspaceData<T>(load: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setData(undefined);
    load().then(value => { if (active) setData(value); }).catch(failure => { if (active) setError(failure instanceof Error ? failure.message : 'Could not load this page.'); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [...dependencies, attempt]);
  return { data, error, loading, refresh: () => setAttempt(value => value + 1) };
}

export default function WorkspacePage({ title, description, children, refresh }: { title: string; description: string; children: ReactNode; refresh?: () => void }) {
  return <DoctorWorkspaceLayout><div className="dw-page-heading"><div><span className="doctor-home-label">YOUR PRACTICE</span><h2>{title}</h2><p>{description}</p></div>{refresh && <button className="dw-secondary" onClick={refresh}><RefreshCw size={15} />Refresh</button>}</div>{children}</DoctorWorkspaceLayout>;
}
export function PageStatus({ loading, error, empty, emptyTitle = 'Nothing here yet', children }: { loading: boolean; error: string; empty?: boolean; emptyTitle?: string; children?: ReactNode }) {
  if (loading) return <div className="dw-panel dw-empty" role="status">Loading your workspace...</div>;
  if (error) return <div className="dw-panel dw-error" role="alert">{error}</div>;
  if (empty) {
    const label = emptyTitle.toLowerCase();
    const Icon = label.includes('patient') ? Users : label.includes('consultation') ? Stethoscope : label.includes('dates') ? CalendarDays : label.includes('prescription') ? FileText : FolderHeart;
    return <div className="dw-panel dw-empty"><div className="dw-empty-visual" aria-hidden="true"><span /><div><Icon size={32} strokeWidth={1.5} /></div><i /></div><h3>{emptyTitle}</h3><p>Shared information will appear here when it becomes available.</p>{label === 'no connected patients yet' && <a className="button primary" href="#doctor-referral-id">Share your referral ID</a>}</div>;
  }
  return <>{children}</>;
}
export function PageSearch({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return <label className="dw-search"><Search size={17} /><input aria-label={placeholder} value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} /></label>;
}
export function ModuleBadge({ module }: { module: string }) { return <span className={`dw-badge ${module}`}>{module === 'child' ? 'Child Care' : module === 'women' ? "Women’s Health" : 'Adult Health'}</span>; }
