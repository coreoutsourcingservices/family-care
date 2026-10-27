import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
async function proxy(request: NextRequest, context: {params: Promise<{path:string[]}>}) {
  const {path} = await context.params;
  if (!path.length || path.some(p => !/^[a-zA-Z0-9_-]+$/.test(p)) || !['admin','superadmin','auth','health'].includes(path[0])) return NextResponse.json({error:{message:'Route not found'}},{status:404});
  const mutating = !['GET','HEAD'].includes(request.method);
  // Never inject CSRF credentials for a cross-origin request.
  if (mutating && (request.headers.get('origin') !== request.nextUrl.origin || request.headers.get('x-requested-with') !== 'FamilyCare')) return NextResponse.json({error:{message:'Request origin rejected'}},{status:403});
  const headers = new Headers({'Content-Type':'application/json', 'X-Auth-Transport':'cookie', 'X-Requested-With':'FamilyCare'});
  headers.set('Cookie', request.headers.get('cookie') || '');
  if (mutating) headers.set('Origin', request.nextUrl.origin);
  const csrf = request.cookies.get('fc_csrf')?.value;
  if (csrf) headers.set('X-CSRF-Token', csrf);
  try {
    const upstream = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:5001'}/api/v1/${path.join('/')}${request.nextUrl.search}`, {method:request.method, headers, body:mutating ? await request.text() : undefined, cache:'no-store', redirect:'manual', signal:AbortSignal.timeout(30000)});
    const data = await upstream.json();
    const csrfToken = data.csrf_token;
    delete data.csrf_token;
    const response = NextResponse.json(data, {status:upstream.status, headers:{'Cache-Control':'no-store'}});
    for (const cookie of upstream.headers.getSetCookie()) {
      response.headers.append('Set-Cookie', cookie.startsWith('fc_access=') ? cookie.replace(/Path=\/api\/v1(?=;|$)/i, 'Path=/') : cookie);
    }
    // Use one header API throughout: mixing cookies.set() with appended Set-Cookie
    // headers would overwrite the upstream access/refresh cookies in NextResponse.
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    if (csrfToken) response.headers.append('Set-Cookie', `fc_csrf=${encodeURIComponent(csrfToken)}; Path=/api/v1; Max-Age=${30*86400}; HttpOnly; SameSite=Lax${secure}`);
    if (upstream.ok && ['logout','logout-all','change-password'].includes(path.at(-1) || '')) {
      response.headers.append('Set-Cookie', 'fc_csrf=; Path=/api/v1; Max-Age=0; HttpOnly; SameSite=Lax');
      response.headers.append('Set-Cookie', 'fc_access=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax');
      response.headers.append('Set-Cookie', 'fc_refresh=; Path=/api/v1/auth; Max-Age=0; HttpOnly; SameSite=Lax');
    }
    return response;
  } catch { return NextResponse.json({error:{message:'Familycare API is unavailable. Please try again shortly.'}},{status:502}); }
}
export { proxy as GET, proxy as POST, proxy as DELETE };
