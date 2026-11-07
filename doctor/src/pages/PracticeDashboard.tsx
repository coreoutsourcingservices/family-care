import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Clock,
  FileText,
  Stethoscope,
  UserPlus,
  Users,
  Zap,
} from "lucide-react";
import PracticeChart from "../components/PracticeChart";
import DoctorWorkspaceLayout from "../components/DoctorWorkspaceLayout";
import { PageStatus, useWorkspaceData } from "../components/WorkspacePage";
import {
  careApi,
  loadConsultations,
  loadPatientRoster as loadPatients,
} from "../lib/workspaceApi";
type Visit = {
  id: string;
  patient_name: string;
  concern: string;
  status: string;
  confirmed_at: string | null;
  requested_at: string;
};
const day = (date: string) => new Date(date).toLocaleDateString("en-CA");
export default function PracticeDashboard() {
  const state = useWorkspaceData("PracticeDashboard:1", async () => {
    const [patients, requests, visits] = await Promise.all([
      loadPatients(),
      loadConsultations(),
      careApi<{ items: Visit[] }>("/doctors/consultation-visits"),
    ]);
    return { patients, requests, visits: visits.items };
  });
  const [tab, setTab] = useState("Today"),
    [range, setRange] = useState(7);
  const patients = state.data?.patients ?? [],
    visits = state.data?.visits ?? [],
    requests = state.data?.requests ?? [];
  const today = day(new Date().toISOString());
  const scheduled = visits
    .filter((v) => v.status === "CONFIRMED" && v.confirmed_at)
    .sort((a, b) => Date.parse(a.confirmed_at!) - Date.parse(b.confirmed_at!));
  const todays = scheduled.filter((v) => day(v.confirmed_at!) === today);
  const groups = [
    ["child", "Child Care", "#7460ff"],
    ["women", "Women's Health", "#f15ab5"],
    ["adult", "Adult Health", "#08c9c7"],
  ];
  const dates = Array.from({ length: range }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - range + 1 + i);
    return d;
  });
  const counts = dates.map(
    (d) =>
      requests.filter((r) => r.date === day(d.toISOString())).length +
      visits.filter((v) => day(v.requested_at) === day(d.toISOString())).length,
  );
  const shown =
    tab === "Today"
      ? todays
      : tab === "Upcoming"
        ? scheduled.filter((v) => day(v.confirmed_at!) > today)
        : visits.filter((v) => v.status === "REQUESTED");
  return (
    <DoctorWorkspaceLayout>
      <div className="dr-dashboard">
        <h2 className="dr-sr-heading">Doctor Dashboard</h2>
        {state.error && (
          <p role="alert" className="dw-error">
            {state.error}
            <button onClick={state.refresh}>Retry</button>
          </p>
        )}
        <section className="dw-panel dr-today">
          <div className="dr-card-heading">
            <div>
              <h2>Today's Consultations</h2>
              <p>Patients scheduled for today</p>
            </div>
            <Link
              className="dr-icon-button"
              aria-label="View today's appointments"
              to="/doctor/appointments"
            >
              <ArrowUpRight />
            </Link>
          </div>
          <PageStatus
            loading={state.loading}
            error={state.error}
            empty={!todays.length}
            emptyTitle="No consultations scheduled today"
          >
            {todays.slice(0, 3).map((v) => (
              <Link
                className="dr-schedule-row"
                key={v.id}
                to="/doctor/appointments"
              >
                <span className="dr-avatar">{v.patient_name.charAt(0)}</span>
                <span>
                  <strong>{v.patient_name}</strong>
                  <small>{v.concern}</small>
                </span>
                <time>
                  {new Date(v.confirmed_at!).toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </time>
              </Link>
            ))}
          </PageStatus>
          <Link className="dr-card-link" to="/doctor/appointments">
            View Full Schedule <ArrowRight size={17} />
          </Link>
        </section>
        <section className="dw-panel dr-clinical">
          <div className="dr-card-heading">
            <div>
              <h2>Clinical Reports</h2>
              <p>Your consultation activity overview</p>
            </div>
            <select
              aria-label="Clinical activity date range"
              value={range}
              onChange={(e) => setRange(Number(e.target.value))}
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>
          <div className="dr-clinical-stats">
            {[
              [Stethoscope, "Consultation requests", requests.length],
              [CalendarDays, "Confirmed appointments", scheduled.length],
              [Users, "Connected patients", patients.length],
            ].map(([Icon, label, count]) => {
              const I = Icon as typeof Users;
              return (
                <div key={String(label)}>
                  <span className="dr-stat-icon">
                    <I />
                  </span>
                  <span>
                    <small>{String(label)}</small>
                    <strong>
                      {state.loading
                        ? "..."
                        : state.error
                          ? "--"
                          : String(count)}
                    </strong>
                  </span>
                </div>
              );
            })}
          </div>
          <PracticeChart
            type="line"
            label="Consultation activity"
            labels={dates.map((d) =>
              d.toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
            )}
            values={counts}
          />
        </section>
        <section className="dw-panel dr-appointments">
          <div className="dr-card-heading">
            <CalendarDays className="dr-blue" />
            <div>
              <h2>Appointments &amp; Consultations</h2>
              <p>Your upcoming and ongoing consultations.</p>
            </div>
            <Link
              className="dr-icon-button"
              aria-label="Manage appointments"
              to="/doctor/appointments"
            >
              <CalendarDays />
            </Link>
          </div>
          <div className="dr-tabs">
            {[
              ["Today", todays.length],
              [
                "Upcoming",
                scheduled.filter((v) => day(v.confirmed_at!) > today).length,
              ],
              [
                "Pending",
                visits.filter((v) => v.status === "REQUESTED").length,
              ],
            ].map(([label, count]) => (
              <button
                key={label}
                className={tab === label ? "active" : ""}
                onClick={() => setTab(String(label))}
              >
                {label} ({count})
              </button>
            ))}
          </div>
          {shown.length ? (
            shown.slice(0, 5).map((v) => (
              <Link
                className="dr-appointment-row"
                to="/doctor/appointments"
                key={v.id}
              >
                <time>
                  {new Date(
                    v.confirmed_at || v.requested_at,
                  ).toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </time>
                <span className="dr-avatar">{v.patient_name.charAt(0)}</span>
                <span>
                  <strong>{v.patient_name}</strong>
                  <small>{v.concern}</small>
                </span>
                <span className="dw-badge">
                  {v.status === "REQUESTED" ? "Pending" : "Confirmed"}
                </span>
              </Link>
            ))
          ) : (
            <p className="dr-empty">
              {state.loading
                ? "Loading appointments..."
                : "No appointments in this view."}
            </p>
          )}
          <Link className="dr-card-link" to="/doctor/appointments">
            View All Appointments <ArrowRight size={17} />
          </Link>
        </section>
        <section className="dw-panel dr-patient-overview">
          <div className="dr-card-heading">
            <Users className="dr-blue" />
            <div>
              <h2>Patient Overview</h2>
              <p>Your connected patient summary.</p>
            </div>
            <Link
              className="dr-icon-button"
              aria-label="View all patients"
              to="/doctor/patients"
            >
              <ArrowUpRight />
            </Link>
          </div>
          <div className="dr-patient-chart">
            <div className="dr-patient-donut">
              <PracticeChart
                type="doughnut"
                label="Patient care areas"
                labels={groups.map((g) => g[1])}
                values={groups.map(
                  (g) => patients.filter((p) => p.module === g[0]).length,
                )}
                colors={groups.map((g) => g[2])}
              />
              <div>
                <strong>{state.loading ? "..." : patients.length}</strong>
                <small>Total Patients</small>
              </div>
            </div>
            <ul>
              {groups.map(([id, label, color]) => {
                const count = patients.filter((p) => p.module === id).length;
                return (
                  <li key={id}>
                    <i style={{ background: color }} />
                    <span>{label}</span>
                    <strong>{count}</strong>
                    <small>
                      {patients.length
                        ? Math.round((count / patients.length) * 100)
                        : 0}
                      %
                    </small>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>
        <section className="dw-panel dr-recent">
          <div className="dr-card-heading">
            <Clock className="dr-blue" />
            <div>
              <h2>Recent Activity</h2>
              <p>Latest requests and updates.</p>
            </div>
          </div>
          {[...visits]
            .sort(
              (a, b) => Date.parse(b.requested_at) - Date.parse(a.requested_at),
            )
            .slice(0, 3)
            .map((v) => (
              <Link
                className="dr-activity-row"
                to="/doctor/consultations"
                key={v.id}
              >
                <CalendarDays size={18} />
                <span>
                  <strong>{v.patient_name}</strong>
                  <small>{v.concern}</small>
                </span>
                <small>{v.status.replaceAll("_", " ")}</small>
              </Link>
            ))}
          {!visits.length && (
            <p className="dr-empty">No recent consultation activity.</p>
          )}
          <Link className="dr-card-link" to="/doctor/consultations">
            View all activity <ArrowRight size={15} />
          </Link>
        </section>
        <section className="dw-panel dr-quick">
          <div className="dr-card-heading">
            <Zap className="dr-blue" />
            <div>
              <h2>Quick Actions</h2>
              <p>Common actions for daily practice.</p>
            </div>
          </div>
          <div>
            {[
              [UserPlus, "View Patients", "patients"],
              [CalendarDays, "Schedule Consultation", "appointments"],
              [FileText, "Create Prescription", "prescriptions"],
              [FileText, "View Reports", "reports"],
            ].map(([Icon, label, path], i) => {
              const I = Icon as typeof Users;
              return (
                <Link
                  className={"dr-quick-" + i}
                  key={String(label)}
                  to={"/doctor/" + path}
                >
                  <I size={30} />
                  <strong>{String(label)}</strong>
                </Link>
              );
            })}
          </div>
        </section>
      </div>
    </DoctorWorkspaceLayout>
  );
}
