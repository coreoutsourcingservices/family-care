import 'server-only';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { Role, User, apiRole, rolePath } from './types';
import {portalCookies} from './portal-session';
export async function requireUser(role: Role): Promise<User> {
  const jar = await cookies();
  const access=jar.get(portalCookies(apiRole(role)).access)?.value;
  if (!access) redirect(`${rolePath(role) || '/'}?session=expired`);
  let response: Response;
  try {
    response = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:5001'}/api/v1/${apiRole(role)}/me`, {headers:{Cookie:`fc_access=${access}`}, cache:'no-store', signal:AbortSignal.timeout(15000)});
  } catch { throw new Error('Familycare API is unavailable. Please check the backend and try again.'); }
  if (response.status === 401 || response.status === 403) redirect(`${rolePath(role) || '/'}?session=expired`);
  if (!response.ok) throw new Error('Unable to verify your session. Please try again.');
  const {user} = await response.json();
  if (user.role !== role) redirect(rolePath(role) || '/');
  return user;
}
