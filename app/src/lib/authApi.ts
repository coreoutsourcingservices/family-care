export type AuthUser = { id: string; public_id: string; referral_id?: string | null; doctor?: import('../../../doctor/src/onboarding/types').DoctorSetupDetails; full_name: string; email?: string; phone_number?: string; role: 'PATIENT' | 'DOCTOR'; approval_status: string };
import type { DoctorAuthFields } from '../../../doctor/src/onboarding/types';
export type AuthResponse = { challenge_token?: string; email_status?: 'sent' | 'queued'; resend_after?: number; expires_in?: number; csrf_token?: string; user?: AuthUser; message?: string } & DoctorAuthFields;

export class ApiError extends Error {
  constructor(message: string, public code: string, public status: number) { super(message); }
}

// Session credentials stay in HttpOnly cookies. Only the CSRF value is readable by JS.
export function publicPortal(path=''): 'patient'|'doctor' {
  if(path.startsWith('/doctors/'))return 'doctor';
  if(path.startsWith('/patients/')||path.startsWith('/children/'))return 'patient';
  return window.location.pathname.startsWith('/doctor')?'doctor':'patient';
}
const refreshInFlight: Partial<Record<'patient'|'doctor',Promise<AuthResponse>>> = {};
export function refreshSession(portal=publicPortal()) {
  return refreshInFlight[portal] ??= authApi('/auth/refresh', undefined, 'POST', false, portal).finally(() => { delete refreshInFlight[portal]; });
}

export async function authApi(path: string, body?: Record<string, unknown>, method: 'POST' | 'GET' = 'POST', retry = true, portal=publicPortal(path)): Promise<AuthResponse> {
  const headers: Record<string, string> = { 'X-Auth-Transport': 'cookie', 'X-Requested-With': 'FamilyCare', 'X-FamilyCare-Portal':portal };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const csrf = sessionStorage.getItem('familycare_csrf_'+portal)??sessionStorage.getItem('familycare_csrf');
  if (csrf) headers['X-CSRF-Token'] = csrf;
  let response: Response;
  try {
    response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1${path}`, {
      method, credentials: 'include', headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(20000),
    });
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection and that the backend is running.', 'network_error', 0);
  }
  let data;
  try { data = await response.json(); } catch { throw new ApiError('The server returned an unexpected response. Please try again.', 'invalid_response', response.status); }
  if (!response.ok) {
    if(data.error?.code==='portal_session_changed')window.location.replace(portal==='doctor'?'/doctor/login':'/customer/login');
    if (response.status === 401 && data.error?.code === 'invalid_token' && retry && path !== '/auth/refresh') {
      await refreshSession(portal);
      return authApi(path, body, method, false, portal);
    }
    const fields = data.error?.fields?.map((field: { field: string }) => field.field.replaceAll('_', ' ')).join(', ');
    throw new ApiError(`${data.error?.message ?? 'Request failed'}${fields ? `: ${fields}` : ''}`, data.error?.code ?? 'request_failed', response.status);
  }
  if (data.csrf_token) sessionStorage.setItem('familycare_csrf_'+portal, data.csrf_token);
  if (path === '/auth/logout') sessionStorage.removeItem('familycare_csrf_'+portal);
  return data;
}
