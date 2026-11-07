import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "../../../app/src/lib/authApi";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  CalendarDays,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Search,
  Settings,
  Stethoscope,
  UserRound,
  Users,
  Menu,
  X,
  HeartPulse,
  CreditCard,
} from "lucide-react";
import {
  clearDoctorWorkspace,
  getDoctorSetup,
  getDoctorWorkspace,
} from "../onboarding/setupSession";
import NotificationCenter from "../notifications/NotificationCenter";
import { disableBrowserPush } from "../notifications/api";
import "../pages/doctor-home.css";
import "../pages/doctor-workspace-design.css";

const clinicalMenu = [
  ["Patients", Users, "/doctor/patients"],
  ["Consultations", Stethoscope, "/doctor/consultations"],
  ["Appointments", CalendarDays, "/doctor/appointments"],
  ["Prescriptions", FileText, "/doctor/prescriptions"],
  ["Clinical Records", ClipboardList, "/doctor/clinical-records"],
  ["Reports", FileText, "/doctor/reports"],
  ["Settings", Settings, "/doctor/settings"],
  ["Subscription", CreditCard, "/doctor/subscription"],
] as const;

const WorkspaceFrameContext = createContext(false);

// Existing page wrappers reuse the persistent route frame.
export default function DoctorWorkspaceLayout({
  children,
}: {
  children: ReactNode;
}) {
  const insideFrame = useContext(WorkspaceFrameContext);
  return insideFrame ? (
    <>{children}</>
  ) : (
    <WorkspaceFrame>{children}</WorkspaceFrame>
  );
}

function WorkspaceFrame({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [, setProfileRevision] = useState(0);
  useEffect(() => {
    const refresh = () => setProfileRevision((n) => n + 1);
    window.addEventListener("familycare:doctor-updated", refresh);
    return () =>
      window.removeEventListener("familycare:doctor-updated", refresh);
  }, []);
  const account = getDoctorWorkspace();
  const setup = getDoctorSetup();
  const pending = account?.user.approval_status === "PENDING_APPROVAL";
  const approved = account?.user.approval_status === "APPROVED";
  const [menu, setMenu] = useState(false);
  useEffect(() => setMenu(false), [location.pathname]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(false);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        document
          .querySelector<HTMLInputElement>(".doctor-header-search input")
          ?.focus();
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);
  const [search, setSearch] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState("");
  const name = account?.user.full_name ?? "Doctor";
  useEffect(() => {
    const manifest = document.createElement("link");
    manifest.rel = "manifest";
    manifest.href = "/doctor.webmanifest";
    document.head.append(manifest);
    const icon = document.createElement("link");
    icon.rel = "apple-touch-icon";
    icon.href = "/doctor-icon-192.png";
    document.head.append(icon);
    return () => {
      manifest.remove();
      icon.remove();
    };
  }, []);
  return (
    <div
      className={
        "doctor-home doctor-workspace " +
        ([
          "/doctor/patients",
          "/doctor/consultations",
          "/doctor/appointments",
          "/doctor/clinical-records",
          "/doctor/reports",
          "/doctor/prescriptions",
          "/doctor/subscription",
        ].includes(location.pathname)
          ? "doctor-reference-page"
          : "")
      }
    >
      <aside
        className={"doctor-home-sidebar " + (menu ? "doctor-menu-open" : "")}
      >
        <button
          className="doctor-nav-close"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        >
          <X />
        </button>
        <Link className="dr-brand" to="/doctor/dashboard">
          <span>
            <HeartPulse size={29} />
          </span>
          <strong>
            FamilyCare<span>+</span>
          </strong>
        </Link>
        <nav aria-label="Doctor workspace">
          <Link
            className={
              location.pathname === "/doctor/dashboard" ? "active" : ""
            }
            to="/doctor/dashboard"
          >
            <LayoutDashboard size={18} />
            Dashboard
          </Link>
          {!approved &&
            (pending ? (
              <button disabled title="Your submitted profile is being reviewed">
                <UserRound size={18} />
                Set My Profile
                <LockKeyhole size={13} />
              </button>
            ) : (
              <Link
                className={
                  location.pathname === "/doctor/setup-account" ? "active" : ""
                }
                to={
                  approved || setup ? "/doctor/setup-account" : "/doctor/login"
                }
              >
                <UserRound size={18} />
                Set My Profile
              </Link>
            ))}
          {clinicalMenu.map(([label, Icon, path]) =>
            approved ? (
              <Link
                key={label}
                className={location.pathname === path ? "active" : ""}
                to={path}
              >
                <Icon size={18} />
                {label}
              </Link>
            ) : (
              <button
                key={label}
                type="button"
                disabled
                title="Available after admin approval"
              >
                <Icon size={18} />
                <span>{label}</span>
                <LockKeyhole size={12} />
              </button>
            ),
          )}
        </nav>
        <button
          className="doctor-sidebar-signout"
          disabled={signingOut}
          onClick={async () => {
            setSigningOut(true);
            setSignOutError("");
            try {
              await disableBrowserPush().catch(() => {});
              if (approved) await authApi("/auth/logout");
              clearDoctorWorkspace();
              navigate("/doctor/login", { replace: true });
            } catch (error) {
              setSignOutError(
                error instanceof Error ? error.message : "Could not sign out",
              );
              setSigningOut(false);
            }
          }}
        >
          <LogOut size={17} />
          Sign out
        </button>
      </aside>
      {menu && (
        <button
          className="doctor-nav-backdrop"
          aria-label="Close menu"
          onClick={() => setMenu(false)}
        />
      )}
      <div className="doctor-workspace-main">
        <header className="doctor-home-header">
          <button
            className="doctor-nav-toggle"
            aria-label="Open navigation"
            aria-expanded={menu}
            onClick={() => setMenu(!menu)}
          >
            <Menu />
          </button>
          <div>
            <span className="doctor-welcome">YOUR CONNECTED PRACTICE</span>
            <h1>
              {location.pathname === "/doctor/dashboard"
                ? `Good ${new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"}, ${name}`
                : clinicalMenu.find(
                    (item) => item[2] === location.pathname,
                  )?.[0] || "Your practice"}{" "}
              <span
                aria-hidden="true"
                hidden={location.pathname !== "/doctor/dashboard"}
              >
                👋
              </span>
            </h1>
            <p>
              {approved
                ? location.pathname === "/doctor/dashboard"
                  ? "Here's your practice overview for today."
                  : location.pathname === "/doctor/patients"
                    ? "Manage and view your connected patients."
                    : location.pathname === "/doctor/consultations"
                      ? "Manage ongoing and past consultations."
                      : location.pathname === "/doctor/appointments"
                        ? "View and manage patient appointments."
                        : location.pathname === "/doctor/clinical-records"
                          ? "Access shared patient records and clinical history."
                          : location.pathname === "/doctor/reports"
                            ? "View and manage shared patient reports."
                            : "Your connected practice workspace."
                : pending
                  ? "Your profile is with the admin for review."
                  : "Complete your profile to start connecting with families."}
            </p>
          </div>
          <div className="doctor-header-tools">
            <form
              className="doctor-header-search"
              onSubmit={(event) => {
                event.preventDefault();
                if (approved) {
                  const reportSearch = location.pathname === "/doctor/reports";
                  const query = new URLSearchParams(
                    reportSearch ? location.search : "",
                  );
                  query.set("search", search);
                  navigate(
                    `${reportSearch ? "/doctor/reports" : "/doctor/patients"}?${query}`,
                  );
                }
              }}
            >
              <Search size={16} />
              <input
                aria-label="Search patients and records"
                placeholder="Search patient, ID, or report..."
                disabled={!approved}
                title={
                  approved
                    ? "Press Enter to search patients"
                    : "Search is available after approval"
                }
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <kbd>Ctrl + K</kbd>
            </form>
            <NotificationCenter />
            <div className="doctor-header-account">
              <span className="doctor-avatar-small">
                {account?.doctor?.images?.profile_photo?.url ? (
                  <img
                    src={account.doctor.images.profile_photo.url}
                    alt="Doctor profile"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      borderRadius: "50%",
                    }}
                  />
                ) : (
                  name.charAt(0)
                )}
              </span>
              <div>
                <strong>{name}</strong>
                <small>
                  {account?.doctor?.specialization || "Doctor account"}
                </small>
              </div>
            </div>
          </div>
        </header>
        <div className="doctor-workspace-content">
          {signOutError && (
            <p className="dw-error" role="alert">
              {signOutError}
            </p>
          )}
          <WorkspaceFrameContext.Provider value={true}>
            {children}
          </WorkspaceFrameContext.Provider>
        </div>
      </div>
    </div>
  );
}
