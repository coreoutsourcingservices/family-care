'use client';
export class ApiError extends Error { constructor(message: string, public status: number) {super(message);} }
let refreshing: Promise<void> | null = null;
export function refreshSession(): Promise<void> {
  if (!refreshing) refreshing = api('auth/refresh', {method:'POST', body:'{}'}, false).then(() => {}).finally(() => {refreshing = null;});
  return refreshing;
}
export async function api<T = Record<string, unknown>>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const response = await fetch('/api/v1/' + path, {...options, credentials: 'same-origin', cache: 'no-store', headers: {'Content-Type': 'application/json', 'X-Requested-With': 'FamilyCare', ...options.headers}});
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 && retry && !path.endsWith('/login') && !path.includes('verify-') && !path.includes('initial-password') && path !== 'auth/refresh') {
    await refreshSession();
    return api<T>(path, options, false);
  }
  if (!response.ok) throw new ApiError(data.error?.message || 'Unable to complete the request. Please try again.', response.status);
  return data as T;
}
export const post = <T = Record<string, unknown>>(path: string, data: unknown = {}) => api<T>(path, {method:'POST', body:JSON.stringify(data)});
