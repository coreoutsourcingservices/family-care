import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthPage from '../../../app/src/pages/auth/AuthPage';
import type { AuthResponse } from '../../../app/src/lib/authApi';
import type { DoctorAuthOutcome } from '../onboarding/types';
import { beginDoctorSetup, clearDoctorSetup, beginDoctorWorkspace, clearDoctorWorkspace } from '../onboarding/setupSession';

// Shared form controls stay shared; doctor-specific response routing lives here.
export default function DoctorAuth({ mode }: { mode: 'signup' | 'login' }) {
  const navigate = useNavigate();
  useEffect(() => { clearDoctorWorkspace(); }, []);

  function handleResult(data: AuthResponse): DoctorAuthOutcome {
    if (data.user?.role !== 'DOCTOR') throw new Error('The server did not return the doctor account. Please sign in again.');
    if (data.requires_profile_setup) {
      beginDoctorSetup(data);
      navigate('/doctor/dashboard', { replace: true });
      return 'setup';
    }
    clearDoctorSetup();
    if (data.user.approval_status === 'PENDING_APPROVAL') {
      if (mode === 'signup') throw new Error('The backend skipped Account Setup. Restart the backend with the latest code, then sign in. Your profile must be completed before submission for approval.');
      beginDoctorWorkspace(data);
      navigate('/doctor/dashboard', { replace: true });
      return 'setup';
    }
    if (data.user.approval_status === 'APPROVED') return 'session';
    throw new Error('The server did not provide the next doctor onboarding step. Please sign in again.');
  }

  return <AuthPage role="doctor" mode={mode} onDoctorResult={handleResult} />;
}
