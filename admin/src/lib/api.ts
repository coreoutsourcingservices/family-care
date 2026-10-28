'use client';
import {currentPortal,portalLogin,type Portal} from './portal-session';
export class ApiError extends Error { constructor(message: string, public status: number) {super(message);} }
const refreshing:Partial<Record<Portal,Promise<void>>>={};
export function refreshSession(portal:Portal=currentPortal()): Promise<void> {
  return refreshing[portal]??=api('auth/refresh', {method:'POST', body:'{}',headers:{'X-FamilyCare-Portal':portal}}, false).then(() => {}).finally(() => {delete refreshing[portal];});
}
export async function api<T = Record<string, unknown>>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers=new Headers(options.headers);
  const namespace=path.split('/')[0];
  const portal:Portal=namespace==='admin'||namespace==='superadmin'?namespace:headers.get('X-FamilyCare-Portal')==='superadmin'?'superadmin':headers.has('X-FamilyCare-Portal')?'admin':currentPortal();
  headers.set('Content-Type','application/json');headers.set('X-Requested-With','FamilyCare');headers.set('X-FamilyCare-Portal',portal);
  const needsSession=((namespace==='admin'||namespace==='superadmin')&&!/\/(login|register|verify-email|verify-login-otp|resend-otp)$/.test(path))||/^auth\/(logout|logout-all|change-password|sessions)(?:\/|$)/.test(path);
  const response = await fetch('/api/v1/' + path, {...options, credentials: 'same-origin', cache: 'no-store', headers});
  const data = await response.json().catch(() => ({}));
  if(response.status===403&&data.error?.code==='forbidden'&&needsSession&&typeof window!=='undefined'){
    window.location.replace(portalLogin(portal,'changed'));
    throw new ApiError('Your session has changed. Please sign in to this portal again.',403);
  }
  if (response.status === 401 && retry && needsSession) {
    try{await refreshSession(portal);return await api<T>(path,{...options,headers},false);}
    catch(error){if(typeof window!=='undefined'&&error instanceof ApiError&&[401,403].includes(error.status))window.location.replace(portalLogin(portal,'expired'));throw error;}
  }
  if (!response.ok) throw new ApiError(data.error?.message || 'Unable to complete the request. Please try again.', response.status);
  return data as T;
}
export const post = <T = Record<string, unknown>>(path: string, data: unknown = {}) => api<T>(path, {method:'POST', body:JSON.stringify(data)});
