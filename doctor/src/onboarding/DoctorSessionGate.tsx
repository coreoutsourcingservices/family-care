import { useEffect, useState } from 'react';
import { Link, Navigate, Outlet, useNavigate } from 'react-router-dom';
import { ApiError, authApi } from '../../../app/src/lib/authApi';
import { beginDoctorWorkspace, clearDoctorWorkspace, getDoctorWorkspace } from './setupSession';
import NotificationProvider from '../notifications/NotificationProvider';
import type { DoctorSetupDetails } from './types';

export default function DoctorSessionGate() {
  const cached = getDoctorWorkspace();
  const [ready, setReady] = useState(!!cached && cached.user.approval_status !== 'APPROVED');
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const navigate = useNavigate();
  useEffect(() => {
    if (ready) return;
    let active = true;
    authApi('/doctors/me', undefined, 'GET').then(data => {
      if (!active) return;
      if (data.user?.role !== 'DOCTOR' || data.user.approval_status !== 'APPROVED') throw new Error('Please sign in with an approved doctor account.');
      const user = data.user as typeof data.user & { doctor?: DoctorSetupDetails };
      beginDoctorWorkspace({ ...data, doctor: user.doctor });
      setReady(true);
    }).catch(failure => {
      if (!active) return;
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) {
        clearDoctorWorkspace(); navigate('/doctor/login', { replace: true });
      } else setError(failure instanceof Error ? failure.message : 'Could not open your workspace.');
    });
    return () => { active = false; };
  }, [attempt, navigate, ready]);
  if (!ready) return <section className="doctor-session-status">{error ? <><p role="alert">{error}</p><button onClick={() => { setError(''); setAttempt(value => value + 1); }}>Try again</button><Link to="/doctor/login">Doctor Login</Link></> : <p role="status">Opening your doctor workspace...</p>}</section>;
  return <NotificationProvider><Outlet /></NotificationProvider>;
}

export function DoctorApprovalGate() {
  return getDoctorWorkspace()?.user.approval_status === 'APPROVED' ? <Outlet /> : <Navigate to="/doctor/dashboard" replace />;
}
