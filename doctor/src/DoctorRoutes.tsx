import { lazy, Suspense } from 'react';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import DoctorAuth from './pages/DoctorAuth';
import DoctorHome from './pages/DoctorHome';
import DoctorSessionGate, { DoctorApprovalGate } from './onboarding/DoctorSessionGate';
import { getDoctorWorkspace } from './onboarding/setupSession';
const AccountSetup = lazy(() => import('./pages/AccountSetup'));
const ProfileDetails = lazy(() => import('./pages/ProfileDetails'));
const Patients = lazy(() => import('./pages/Patients'));
const Consultations = lazy(() => import('./pages/Consultations'));
const ClinicalRecords = lazy(() => import('./pages/ClinicalRecords'));
const Appointments = lazy(() => import('./pages/Appointments'));
const Prescriptions = lazy(() => import('./pages/Prescriptions'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));
const VaccineReviews = lazy(() => import('./pages/VaccineReviews'));

function ProfileRoute() {
  const status = getDoctorWorkspace()?.user.approval_status;
  return status === 'APPROVED' || status === 'PENDING_APPROVAL' ? <ProfileDetails /> : <AccountSetup />;
}
export default function DoctorRoutes() {
  return <Suspense fallback={<p className="doctor-session-status" role="status">Opening doctor workspace...</p>}><Routes>
    <Route path="signup" element={<DoctorAuth key="doctor-signup" mode="signup" />} />
    <Route path="login" element={<DoctorAuth key="doctor-login" mode="login" />} />
    <Route element={<DoctorSessionGate />}>
      <Route path="dashboard" element={<DoctorHome />} />
      <Route path="setup-account" element={<ProfileRoute />} />
      <Route element={<DoctorApprovalGate />}>
        <Route path="patients" element={<Patients />} />
        <Route path="consultations" element={<Consultations />} />
        <Route path="clinical-records" element={<ClinicalRecords />} />
        <Route path="appointments" element={<Appointments />} />
        <Route path="prescriptions" element={<Prescriptions />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
        <Route path="vaccination-reviews" element={<VaccineReviews />} />
      </Route>
    </Route>
    <Route index element={<Navigate to="/doctor/dashboard" replace />} />
    <Route path="*" element={<section className="doctor-session-status"><h1>Page not found</h1><Link to="/doctor/dashboard">Doctor dashboard</Link></section>} />
  </Routes></Suspense>;
}
