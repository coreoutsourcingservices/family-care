import { ApiError } from '../../../app/src/lib/authApi';

export type ImageKind = 'profile_photo' | 'degree_photo';

export async function uploadSetupImage(token: string, kind: ImageKind, file: File) {
  const body = new FormData();
  body.set('setup_token', token); body.set('kind', kind); body.set('file', file);
  let response: Response;
  try {
    response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/doctors/setup-images`, {
      method: 'POST', body, credentials: 'include',
      headers: { 'X-Requested-With': 'FamilyCare', 'X-Auth-Transport': 'cookie' }, signal: AbortSignal.timeout(45000),
    });
  } catch { throw new ApiError('Could not upload the image. Check your connection and try again.', 'network_error', 0); }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(data?.error?.message ?? 'Image upload failed. Please try again.', data?.error?.code ?? 'upload_failed', response.status);
  return data;
}
