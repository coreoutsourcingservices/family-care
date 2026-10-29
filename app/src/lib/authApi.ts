export type AuthUser = { id: string; public_id: string; full_name: string; email?: string; phone_number?: string; role: 'PATIENT' | 'DOCTOR'; approval_status: string };
export type AuthResponse = { setup_token?: string; requires_profile_setup?: boolean; doctor?: Record<string, string | number | null>; rejection_reason?: string; challenge_token?: string; email_status?: 'sent' | 'queued'; resend_after?: number; expires_in?: number; csrf_token?: string; user?: AuthUser; message?: string };

export class ApiError extends Error {
  constructor(message: string, public code: string, public status: number) { super(message); }
}

// Session credentials stay in HttpOnly cookies. Only the CSRF value is readable by JS.
let refreshInFlight: Promise<AuthResponse> | undefined;
export function refreshSession() {
  return refreshInFlight ??= authApi('/auth/refresh', undefined, 'POST', false).finally(() => { refreshInFlight = undefined; });
}

export async function authApi(path: string, body?: Record<string, unknown>, method: 'POST' | 'GET' = 'POST', retry = true): Promise<AuthResponse> {
  const headers: Record<string, string> = { 'X-Auth-Transport': 'cookie', 'X-Requested-With': 'FamilyCare' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const csrf = sessionStorage.getItem('familycare_csrf');
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
    if (response.status === 401 && data.error?.code === 'invalid_token' && retry && path !== '/auth/refresh') {
      await refreshSession();
      return authApi(path, body, method, false);
    }
    const fields = data.error?.fields?.map((field: { field: string }) => field.field.replaceAll('_', ' ')).join(', ');
    throw new ApiError(`${data.error?.message ?? 'Request failed'}${fields ? `: ${fields}` : ''}`, data.error?.code ?? 'request_failed', response.status);
  }
  if (data.csrf_token) sessionStorage.setItem('familycare_csrf', data.csrf_token);
  if (path === '/auth/logout') sessionStorage.removeItem('familycare_csrf');
  return data;
}
