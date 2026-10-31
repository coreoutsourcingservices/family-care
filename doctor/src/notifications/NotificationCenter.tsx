import { useEffect, useRef, useState } from 'react';
import { Bell, BellOff, Check, X } from 'lucide-react';
import { useDoctorNotifications } from './NotificationProvider';
import { disableBrowserPush, notificationApi } from './api';

export function NotificationPreferences() {
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const supported = typeof Notification !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && window.isSecureContext;
  useEffect(() => {
    let active = true;
    async function sync() {
      if (!supported) return;
      const registration = await navigator.serviceWorker.getRegistration('/doctor/');
      const subscription = await registration?.pushManager.getSubscription();
      if (active) setEnabled(Notification.permission === 'granted' && !!subscription);
    }
    void sync().catch(() => {});
    const handle = () => { void sync().catch(() => { if (active) setEnabled(false); }); };
    window.addEventListener('doctor-push-preferences', handle);
    window.addEventListener('focus', handle);
    return () => { active = false; window.removeEventListener('doctor-push-preferences', handle); window.removeEventListener('focus', handle); };
  }, [supported]);
  async function toggle() {
    setBusy(true); setError('');
    try {
      if (enabled) { await disableBrowserPush(); setEnabled(false); return; }
      // Keep this prompt inside the user's click; iOS requires a direct gesture.
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') throw new Error('Notifications are blocked. Allow them in your browser’s site settings.');
      const config = await notificationApi<{ enabled: boolean; public_key: string }>('/push-config');
      if (!config.enabled || !config.public_key) throw new Error('Browser push is not configured on this server yet.');
      const registration = await navigator.serviceWorker.register('/doctor-sw.js', { scope: '/doctor/' });
      await navigator.serviceWorker.ready;
      const raw = atob(config.public_key.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - config.public_key.length % 4) % 4));
      const key = new Uint8Array(raw.length); for (let index = 0; index < raw.length; index++) key[index] = raw.charCodeAt(index);
      let subscription = await registration.pushManager.getSubscription();
      const created = !subscription;
      subscription ??= await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
      try { await notificationApi('/subscriptions', subscription.toJSON() as Record<string, unknown>); }
      catch (failure) { if (created) await subscription.unsubscribe(); throw failure; }
      setEnabled(true); window.dispatchEvent(new Event('doctor-push-preferences'));
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not change notification settings.'); }
    finally { setBusy(false); }
  }
  return <section className="doctor-push-preferences"><div><strong>Browser &amp; mobile notifications</strong><p>{supported ? enabled ? 'Enabled on this browser, including supported background notifications.' : 'Receive account and practice updates on this device.' : 'Use HTTPS on mobile. On iPhone, add the website to your Home Screen first.'}</p></div><button className="dw-secondary" disabled={!supported || busy} onClick={() => { void toggle(); }}>{enabled ? <BellOff size={14} /> : <Bell size={14} />}{busy ? 'Please wait...' : enabled ? 'Disable on this device' : 'Enable notifications'}</button>{error && <p className="dw-error" role="alert">{error}</p>}</section>;
}

export default function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const inbox = useDoctorNotifications();
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); };
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpen(false); root.current?.querySelector<HTMLButtonElement>('button')?.focus(); } };
    document.addEventListener('pointerdown', close); document.addEventListener('keydown', key);
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', key); };
  }, [open]);
  return <div className="doctor-notification-root" ref={root}><button className="doctor-notification-bell" aria-label={`Notifications${inbox?.unread ? ` (${inbox.unread} unread)` : ''}`} aria-expanded={open} aria-controls="doctor-notification-panel" onClick={() => { setOpen(value => !value); void inbox?.refresh(); }}><Bell size={20} />{!!inbox?.unread && <b>{inbox.unread > 99 ? '99+' : inbox.unread}</b>}</button>{open && <section id="doctor-notification-panel" className="doctor-notification-panel" aria-label="Notifications"><header><div><h2>Notifications</h2><small aria-live="polite">{inbox?.connection}</small></div><button aria-label="Close notifications" onClick={() => setOpen(false)}><X size={17} /></button></header>{inbox?.error && <p className="dw-error" role="alert">{inbox.error}</p>}<div className="doctor-inbox-list">{inbox?.items.length ? inbox.items.map(item => <button key={item.id} className={item.read_at ? 'read' : ''} onClick={() => { void inbox.open(item).then(success => { if (success) setOpen(false); }); }}><span>{item.read_at ? <Check size={15} /> : <Bell size={15} />}</span><div><strong>{item.title}</strong><p>{item.body}</p><time>{new Date(item.created_at).toLocaleString('en-IN')}</time></div></button>) : <p className="doctor-inbox-empty">You’re all caught up. Account updates will appear here.</p>}</div><NotificationPreferences /></section>}</div>;
}
