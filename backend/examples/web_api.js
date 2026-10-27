// API client only. No UI. Configure the actual backend origin on deployment.
const base = 'http://127.0.0.1:5001';
let csrfToken = null;
let refreshInFlight = null;

export async function api(path, method = 'GET', body, retry = true) {
  const headers = {'X-Auth-Transport': 'cookie', 'X-Requested-With': 'FamilyCare'};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
  const response = await fetch(base + path, {
    method, headers, credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  const expiredSession = ['invalid_token', 'session_revoked'].includes(data.error?.code);
  if (response.status === 401 && expiredSession && retry && !path.includes('/auth/refresh')) {
    refreshInFlight ??= api('/api/v1/auth/refresh', 'POST', undefined, false)
      .finally(() => { refreshInFlight = null; });
    await refreshInFlight;
    return api(path, method, body, false);
  }
  if (!response.ok) throw Object.assign(new Error(data.error?.message || 'API failed'), {status: response.status, data});
  if (data.csrf_token) {
    csrfToken = data.csrf_token;
    // CSRF token is not an authentication credential; persist to survive page reloads.
    sessionStorage.setItem('familycare_csrf', csrfToken);
  }
  if (path === '/api/v1/auth/logout' || path === '/api/v1/auth/logout-all') {
    csrfToken = null; sessionStorage.removeItem('familycare_csrf');
  }
  return data;
}

export function restoreCsrf() { csrfToken = sessionStorage.getItem('familycare_csrf'); }
// Example flow: register -> verify-email -> approval (if needed) -> email/password login.
// Admin/doctor register verification returns pending approval, with no session.
