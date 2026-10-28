import { ApiError, refreshSession } from './authApi';

export async function careApi<T>(path: string, body?: FormData | Record<string, unknown>, retry = true, method?: 'GET' | 'POST' | 'PUT'): Promise<T> {
  const headers: Record<string, string> = { 'X-Auth-Transport': 'cookie', 'X-Requested-With': 'FamilyCare' };
  const multipart = body instanceof FormData;
  if (body && !multipart) headers['Content-Type'] = 'application/json';
  const csrf = sessionStorage.getItem('familycare_csrf');
  if (csrf) headers['X-CSRF-Token'] = csrf;
  let response: Response;
  try {
    response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1${path}`, {
      method: method ?? (body ? 'POST' : 'GET'), credentials: 'include', headers, body: body ? multipart ? body as FormData : JSON.stringify(body) : undefined, signal: AbortSignal.timeout(body ? 120000 : 20000),
    });
  } catch { throw new ApiError('Cannot reach the server. Check your connection and try again.', 'network_error', 0); }
  let data;
  try { data = await response.json(); } catch { throw new ApiError('Unexpected server response. Check that the backend is updated and running.', 'invalid_response', response.status); }
  if (!response.ok) {
    if (response.status === 401 && data.error?.code === 'invalid_token' && retry) {
      await refreshSession(); return careApi(path, body, false, method);
    }
    const fields = data.error?.fields?.map((field: { field: string }) => field.field).join(', ');
    throw new ApiError(`${data.error?.message ?? 'Request failed'}${fields ? `: ${fields}` : ''}`, data.error?.code ?? 'request_failed', response.status);
  }
  return data;
}
