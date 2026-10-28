import { NextRequest, NextResponse } from 'next/server';
import {portalCookies, type Portal} from '@/lib/portal-session';
export const dynamic = 'force-dynamic';
async function proxy(request: NextRequest, context: {params: Promise<{path:string[]}>}) {
  const {path} = await context.params;
  if (!path.length || path.some(p => !/^[a-zA-Z0-9_-]+$/.test(p)) || !['admin','superadmin','auth','health','localization'].includes(path[0])) return NextResponse.json({error:{message:'Route not found'}},{status:404});
  const mutating = !['GET','HEAD'].includes(request.method);
  const requestedPortal=request.headers.get('x-familycare-portal');
  if(requestedPortal&&!['admin','superadmin'].includes(requestedPortal)) return NextResponse.json({error:{message:'Invalid portal'}},{status:400});
  const portal:Portal=path[0]==='superadmin'?'superadmin':path[0]==='admin'?'admin':requestedPortal==='superadmin'?'superadmin':'admin';
  const names=portalCookies(portal);
  // Host preserves the browser's authority when Next normalizes loopback URLs.
  const requestOrigin=`${request.nextUrl.protocol}//${request.headers.get('host')||request.nextUrl.host}`;
  // Never inject CSRF credentials for a cross-origin request.
  if (mutating && (request.headers.get('origin') !== requestOrigin || request.headers.get('x-requested-with') !== 'FamilyCare')) return NextResponse.json({error:{message:'Request origin rejected'}},{status:403});
  const headers = new Headers({'Content-Type':'application/json', 'X-Auth-Transport':'cookie', 'X-Requested-With':'FamilyCare'});
  // Enable only behind a reverse proxy that overwrites this header.
  if (path[0] === 'localization' && process.env.GEO_FORWARD_CLIENT_IP === 'true') {
    const forwarded = request.headers.get('x-forwarded-for');
    if (forwarded) headers.set('X-Forwarded-For', forwarded);
  }
  // Translate only this portal's cookies to Flask's names. Patient cookies and
  // the other portal's credentials must never be forwarded by this proxy.
  const upstreamCookies=[['fc_access',names.access],['fc_refresh',names.refresh]].flatMap(([name,key])=>{
    const value=request.cookies.get(key)?.value;return value?[`${name}=${value}`]:[];
  });
  headers.set('Cookie',upstreamCookies.join('; '));
  if (mutating) headers.set('Origin', requestOrigin);
  const csrf = request.cookies.get(names.csrf)?.value;
  if (csrf) headers.set('X-CSRF-Token', csrf);
  try {
    const upstream = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:5001'}/api/v1/${path.join('/')}${request.nextUrl.search}`, {method:request.method, headers, body:mutating ? await request.text() : undefined, cache:'no-store', redirect:'manual', signal:AbortSignal.timeout(30000)});
    const data = await upstream.json();
    const csrfToken = data.csrf_token;
    delete data.csrf_token;
    const response = NextResponse.json(data, {status:upstream.status, headers:{'Cache-Control':'no-store'}});
    for (const cookie of upstream.headers.getSetCookie()) {
      if(!/^fc_(access|refresh)=/.test(cookie))continue;
      const renamed=cookie.replace(/^fc_access=/,`${names.access}=`).replace(/^fc_refresh=/,`${names.refresh}=`);
      response.headers.append('Set-Cookie', cookie.startsWith('fc_access=') ? renamed.replace(/Path=\/api\/v1(?=;|$)/i, 'Path=/') : renamed);
    }
    // Use one header API throughout: mixing cookies.set() with appended Set-Cookie
    // headers would overwrite the upstream access/refresh cookies in NextResponse.
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    if (csrfToken) response.headers.append('Set-Cookie', `${names.csrf}=${encodeURIComponent(csrfToken)}; Path=/api/v1; Max-Age=${30*86400}; HttpOnly; SameSite=Lax${secure}`);
    if (upstream.ok && ['logout','logout-all','change-password'].includes(path.at(-1) || '')) {
      response.headers.append('Set-Cookie', `${names.csrf}=; Path=/api/v1; Max-Age=0; HttpOnly; SameSite=Lax`);
      response.headers.append('Set-Cookie', `${names.access}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`);
      response.headers.append('Set-Cookie', `${names.refresh}=; Path=/api/v1/auth; Max-Age=0; HttpOnly; SameSite=Lax`);
    }
    return response;
  } catch { return NextResponse.json({error:{message:'Familycare API is unavailable. Please try again shortly.'}},{status:502}); }
}
export { proxy as GET, proxy as POST, proxy as DELETE, proxy as PUT, proxy as PATCH };
