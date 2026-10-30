import type { AuthResponse, AuthUser } from '../../../app/src/lib/authApi';
import type { DoctorSetupDetails } from './types';

export type DoctorSetupSession = {
  token: string;
  user: AuthUser;
  doctor: DoctorSetupDetails | undefined;
  rejectionReason: string | null;
  expiresAt: number;
};

// Setup tokens authorize only onboarding, never clinical APIs. Keep them out of
// URLs, browser storage and history state. After reload, sign in to resume.
let session: DoctorSetupSession | null = null;
let workspace: (Pick<DoctorSetupSession, 'user' | 'doctor' | 'rejectionReason'> & { notificationToken?: string }) | null = null;

export function beginDoctorWorkspace(response: AuthResponse) {
  if (response.user?.role !== 'DOCTOR') throw new Error('Doctor account required');
  workspace = { user: response.user, doctor: response.doctor, rejectionReason: response.rejection_reason ?? null, notificationToken: response.notification_token };
}

export function getDoctorWorkspace() { return workspace; }
export function setDoctorNotificationToken(token: string) { if (workspace) workspace = { ...workspace, notificationToken: token }; }
export function clearDoctorWorkspace() { session = null; workspace = null; }
export function markDoctorPending(doctor?: DoctorSetupDetails) {
  if (workspace) workspace = { ...workspace, doctor: doctor ?? workspace.doctor, user: { ...workspace.user, approval_status: 'PENDING_APPROVAL' } };
  session = null;
}

export function beginDoctorSetup(response: AuthResponse) {
  if (!response.requires_profile_setup || !response.setup_token || response.user?.role !== 'DOCTOR') {
    throw new Error('The server did not return a doctor setup session. Please sign in again.');
  }
  session = {
    token: response.setup_token,
    user: response.user,
    doctor: response.doctor,
    rejectionReason: response.rejection_reason ?? null,
    expiresAt: Date.now() + 30 * 60 * 1000,
  };
  beginDoctorWorkspace(response);
}

export function getDoctorSetup() {
  if (session && session.expiresAt <= Date.now()) session = null;
  return session;
}

export function clearDoctorSetup() { session = null; }
