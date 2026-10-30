import { ApiError, authApi } from '../../../app/src/lib/authApi';
import { getDoctorWorkspace, setDoctorNotificationToken } from '../onboarding/setupSession';

export type DoctorNotice = { id: string; kind: string; title: string; body: string; path: string; created_at: string; read_at: string | null };
export async function notificationApi<T>(path: string, body?: Record<string, unknown>, method = body ? 'POST' : 'GET', retry = true): Promise<T> {
  let token = getDoctorWorkspace()?.notificationToken;
  if (!token) throw new ApiError('Sign in again to enable account notifications.', 'notification_session_required', 401);
  let response: Response;
  try {
    response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/doctors/notifications${path}`, {
      method, headers: { Authorization: `Bearer ${token}`, ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(15000),
    });
  } catch { throw new Error('Could not reach the notification service. Try again.'); }
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && retry && getDoctorWorkspace()?.user.approval_status === 'APPROVED') {
      const session = await authApi('/doctors/me', undefined, 'GET');
      if (session.notification_token) { setDoctorNotificationToken(session.notification_token); return notificationApi(path, body, method, false); }
    }
    throw new ApiError(data.error?.message ?? 'Could not load notifications.', data.error?.code ?? 'notification_error', response.status);
  }
  return data;
}

export async function disableBrowserPush() {
  if (!('serviceWorker' in navigator)) return;
  const registration = await navigator.serviceWorker.getRegistration('/doctor/');
  const subscription = await registration?.pushManager.getSubscription();
  if (subscription) {
    try { await notificationApi('/subscriptions', { endpoint: subscription.endpoint }, 'DELETE'); }
    finally { await subscription.unsubscribe(); }
  }
  window.dispatchEvent(new Event('doctor-push-preferences'));
}
