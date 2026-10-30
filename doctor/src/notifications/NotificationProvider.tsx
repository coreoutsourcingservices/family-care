import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';
import { getDoctorWorkspace } from '../onboarding/setupSession';
import { notificationApi } from './api';
import type { DoctorNotice } from './api';

type InboxState = { items: DoctorNotice[]; unread: number; error: string; refresh: () => Promise<void>; open: (notice: DoctorNotice) => Promise<boolean> };
const Inbox = createContext<InboxState | null>(null);
export const useDoctorNotifications = () => useContext(Inbox);

export default function NotificationProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<DoctorNotice[]>([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState('');
  const [toast, setToast] = useState<DoctorNotice>();
  const seen = useRef<Set<string> | null>(null);
  const active = useRef(true);
  const inFlight = useRef(false);
  const navigate = useNavigate();
  const refresh = useCallback(async () => {
    if (!getDoctorWorkspace()?.notificationToken || inFlight.current) return;
    inFlight.current = true;
    try {
      const data = await notificationApi<{ items: DoctorNotice[]; unread: number }>('?per_page=25');
      if (!active.current) return;
      if (seen.current) {
        const latest = data.items.find(item => !item.read_at && !seen.current!.has(item.id));
        if (latest) setToast(latest);
      }
      seen.current = new Set([...(seen.current ?? []), ...data.items.map(item => item.id)]);
      setItems(data.items); setUnread(data.unread); setError('');
    } catch (failure) { if (active.current) setError(failure instanceof Error ? failure.message : 'Notifications unavailable.'); }
    finally { inFlight.current = false; }
  }, []);
  useEffect(() => {
    active.current = true;
    void refresh();
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') void refresh(); }, 30000);
    const focus = () => { void refresh(); };
    const message = (event: MessageEvent) => { if (event.data?.type === 'doctor-push') void refresh(); };
    window.addEventListener('focus', focus);
    document.addEventListener('visibilitychange', focus);
    navigator.serviceWorker?.addEventListener('message', message);
    return () => { active.current = false; clearInterval(timer); window.removeEventListener('focus', focus); document.removeEventListener('visibilitychange', focus); navigator.serviceWorker?.removeEventListener('message', message); };
  }, [refresh]);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(undefined), 9000); return () => clearTimeout(timer); }, [toast]);
  async function open(notice: DoctorNotice) {
    try {
      await notificationApi(`/${notice.id}/read`, {}, 'POST');
      setToast(undefined); await refresh();
      const path = notice.path.startsWith('/doctor/') && !notice.path.startsWith('//') ? notice.path : '/doctor/dashboard';
      navigate(path); return true;
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not open this notification.'); return false; }
  }
  return <Inbox.Provider value={{ items, unread, error, refresh, open }}>{children}{toast && <div className="doctor-notice-toast" role="status"><div><strong>{toast.title}</strong><p>{toast.body}</p><button onClick={() => { void open(toast); }}>Open notification →</button></div><button aria-label="Dismiss notification" onClick={() => setToast(undefined)}><X size={16} /></button></div>}</Inbox.Provider>;
}
