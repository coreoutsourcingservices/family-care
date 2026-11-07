import { lazy, Suspense } from "react";
import { Link, Navigate, Outlet, Route, Routes } from "react-router-dom";
import DoctorWorkspaceLayout from "./components/DoctorWorkspaceLayout";
import DoctorAuth from "./pages/DoctorAuth";
import DoctorHome from "./pages/DoctorHome";
import DoctorSessionGate, {
  DoctorApprovalGate,
} from "./onboarding/DoctorSessionGate";
import { getDoctorWorkspace } from "./onboarding/setupSession";
const AccountSetup = lazy(() => import("./pages/AccountSetup"));
const ProfileDetails = lazy(() => import("./pages/ProfileDetails"));
const PatientOverview = lazy(() => import("./pages/PatientOverview"));
const SharedAdultWorkspace = lazy(
  () => import("../../customer/src/modules/adult/SharedAdultWorkspace"),
);
const SharedWomenWorkspace = lazy(
  () => import("../../customer/src/modules/women/SharedWomenWorkspace"),
);
const Patients = lazy(() => import("./pages/Patients"));
const Consultations = lazy(() => import("./pages/Consultations"));
const ClinicalRecords = lazy(() => import("./pages/ClinicalRecords"));
const Appointments = lazy(() => import("./pages/Appointments"));
const Prescriptions = lazy(() => import("./pages/Prescriptions"));
const Reports = lazy(() => import("./pages/Reports"));
const DoctorHandoffs = lazy(() => import("./pages/DoctorHandoffs"));
const Subscription = lazy(() => import("./pages/Subscription"));
const Settings = lazy(() => import("./pages/Settings"));
const ChildCare = lazy(() => import("./pages/ChildCare"));
const Vaccination = lazy(() => import("./pages/Vaccination"));
const VaccineReviews = lazy(() => import("./pages/VaccineReviews"));

function ProfileRoute() {
  const status = getDoctorWorkspace()?.user.approval_status;
  return status === "APPROVED" || status === "PENDING_APPROVAL" ? (
    <ProfileDetails />
  ) : (
    <AccountSetup />
  );
}
function WorkspaceRoute() {
  return (
    <DoctorWorkspaceLayout>
      <Suspense
        fallback={
          <div role="status" className="dw-panel dw-empty">
            Loading page...
          </div>
        }
      >
        <Outlet />
      </Suspense>
    </DoctorWorkspaceLayout>
  );
}
export default function DoctorRoutes() {
  return (
    <Suspense
      fallback={
        <p className="doctor-session-status" role="status">
          Opening doctor workspace...
        </p>
      }
    >
      <Routes>
        <Route
          path="signup"
          element={<DoctorAuth key="doctor-signup" mode="signup" />}
        />
        <Route
          path="login"
          element={<DoctorAuth key="doctor-login" mode="login" />}
        />
        <Route element={<DoctorSessionGate />}>
          <Route element={<WorkspaceRoute />}>
            <Route path="dashboard" element={<DoctorHome />} />
            <Route path="setup-account" element={<ProfileRoute />} />
            <Route element={<DoctorApprovalGate />}>
              <Route path="child-care" element={<ChildCare />} />
              <Route path="vaccination" element={<Vaccination />} />
              <Route path="patients" element={<Patients />} />
              <Route path="patients/:profileId" element={<PatientOverview />} />
              <Route path="consultations" element={<Consultations />} />
              <Route path="clinical-records" element={<ClinicalRecords />} />
              <Route path="appointments" element={<Appointments />} />
              <Route path="prescriptions" element={<Prescriptions />} />
              <Route path="reports" element={<Reports />} />
              <Route path="referrals" element={<DoctorHandoffs />} />
              <Route path="settings" element={<Settings />} />
              <Route path="subscription" element={<Subscription />} />
              <Route path="vaccination-reviews" element={<VaccineReviews />} />
            </Route>
          </Route>
          <Route element={<DoctorApprovalGate />}>
            <Route
              path="adult/:profileId"
              element={
                <Suspense fallback={<p role="status">Loading patient...</p>}>
                  <SharedAdultWorkspace />
                </Suspense>
              }
            />
            <Route
              path="women/:profileId"
              element={
                <Suspense fallback={<p role="status">Loading patient...</p>}>
                  <SharedWomenWorkspace />
                </Suspense>
              }
            />
          </Route>
        </Route>
        <Route index element={<Navigate to="/doctor/dashboard" replace />} />
        <Route
          path="*"
          element={
            <section className="doctor-session-status">
              <h1>Page not found</h1>
              <Link to="/doctor/dashboard">Doctor dashboard</Link>
            </section>
          }
        />
      </Routes>
    </Suspense>
  );
}
