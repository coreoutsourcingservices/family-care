import { useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Stethoscope } from "lucide-react";
import WorkspacePage, {
  PageSearch,
  PageStatus,
  useWorkspaceData,
  ModuleBadge,
} from "../components/WorkspacePage";
import {
  loadConsultations,
  loadPatients,
  loadRecords,
  loadReports,
} from "../lib/workspaceApi";
export default function Consultations() {
  const state = useWorkspaceData("Consultations:1", async () => {
    const [requests, patients] = await Promise.all([
      loadConsultations(),
      loadPatients(),
    ]);
    return { requests, patients };
  });
  const [search, setSearch] = useState(""),
    [status, setStatus] = useState("all"),
    [selected, setSelected] = useState(""),
    [tab, setTab] = useState("Consultation");
  const rows =
    state.data?.requests.filter(
      (r) =>
        (status === "all" || r.status === status) &&
        `${r.title} ${state.data?.patients.find((p) => p.id === r.child_id)?.full_name ?? ""}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    ) ?? [];
  const current = rows.find((r) => r.id === selected) ?? rows[0];
  const patient = state.data?.patients.find((p) => p.id === current?.child_id);
  const history = useWorkspaceData("Consultations:2",
    () => (current ? loadRecords(current.child_id) : Promise.resolve([])),
    [current?.child_id],
  );
  const reports = useWorkspaceData("Consultations:3",
    () => (current ? loadReports(current.child_id) : Promise.resolve([])),
    [current?.child_id],
  );
  return (
    <WorkspacePage
      title="Consultations"
      description="Manage ongoing and past consultations."
      refresh={state.refresh}
    >
      <div className="dw-toolbar">
        <PageSearch
          value={search}
          onChange={setSearch}
          placeholder="Search consultation requests"
        />
      </div>
      <div
        className="dr-patient-tabs"
        role="group"
        aria-label="Consultation status"
      >
        <button
          className={status === "all" ? "active" : ""}
          onClick={() => setStatus("all")}
        >
          All ({state.data?.requests.length ?? 0})
        </button>
        {[
          ...new Set(state.data?.requests.map((r) => r.status || "REQUESTED")),
        ].map((s) => (
          <button
            className={status === s ? "active" : ""}
            key={s}
            onClick={() => setStatus(s)}
          >
            {s.replaceAll("_", " ")} (
            {state.data?.requests.filter((r) => r.status === s).length})
          </button>
        ))}
      </div>
      <PageStatus
        loading={state.loading}
        error={state.error}
        empty={!rows.length}
        emptyTitle="No matching consultation requests"
      >
        <div className="dr-consultation-layout">
          <aside className="dw-panel dr-consultation-list">
            {rows.map((r) => (
              <button
                key={r.id}
                className={current?.id === r.id ? "active" : ""}
                onClick={() => {
                  setSelected(r.id);
                  setTab("Consultation");
                }}
              >
                <span className="dr-avatar">
                  {(
                    state.data?.patients.find((p) => p.id === r.child_id)
                      ?.full_name ?? "P"
                  ).charAt(0)}
                </span>
                <span>
                  <strong>
                    {state.data?.patients.find((p) => p.id === r.child_id)
                      ?.full_name ?? "Shared profile"}
                  </strong>
                  <small>
                    {r.date} - {r.title}
                  </small>
                </span>
                <small>{r.status.replaceAll("_", " ")}</small>
              </button>
            ))}
          </aside>
          {current && (
            <section className="dw-panel dr-consultation-detail">
              <div className="dr-card-heading">
                <span className="dr-avatar">
                  {patient?.full_name.charAt(0) ?? "P"}
                </span>
                <div>
                  <h2>{patient?.full_name ?? "Shared profile"}</h2>
                  <p>Patient ID: {current.child_id}</p>
                </div>
                {patient && <ModuleBadge module={patient.module} />}
              </div>
              <div className="dr-tabs">
                {["Consultation", "History", "Reports", "Prescriptions"].map(
                  (t) => (
                    <button
                      className={tab === t ? "active" : ""}
                      key={t}
                      onClick={() => setTab(t)}
                    >
                      {t}
                    </button>
                  ),
                )}
              </div>
              {tab === "Consultation" ? (
                <div className="dr-consultation-body">
                  <section>
                    <h3>Reason for visit</h3>
                    <p>{current.title}</p>
                    <h3>Shared notes</h3>
                    <p>{current.notes || "No notes provided."}</p>
                    <h3>Requested date</h3>
                    <p>{current.date}</p>
                    <span className="dw-badge">
                      {current.status.replaceAll("_", " ")}
                    </span>
                  </section>
                  <aside>
                    <h3>
                      <Stethoscope size={17} /> Recorded vitals
                    </h3>
                    {[
                      ["Systolic", current.systolic, "mmHg"],
                      ["Diastolic", current.diastolic, "mmHg"],
                      ["Pulse", current.pulse, "bpm"],
                      ["Glucose", current.glucose, "mg/dL"],
                    ]
                      .filter(([, v]) => v != null)
                      .map(([label, value, unit]) => (
                        <p key={label}>
                          <span>{label}</span>
                          <strong>
                            {value} {unit}
                          </strong>
                        </p>
                      ))}
                    {[current.systolic, current.pulse, current.glucose].every(
                      (v) => v == null,
                    ) && <p>No vitals recorded in this request.</p>}
                  </aside>
                </div>
              ) : tab === "History" ? (
                <PageStatus
                  loading={history.loading}
                  error={history.error}
                  empty={!history.data?.length}
                  emptyTitle="No shared history"
                >
                  {history.data?.map((r) => (
                    <article className="dr-detail-entry" key={r.id}>
                      <small>{r.date}</small>
                      <h3>{r.title}</h3>
                      <p>{r.notes || "No additional notes."}</p>
                    </article>
                  ))}
                </PageStatus>
              ) : (
                <PageStatus
                  loading={reports.loading}
                  error={reports.error}
                  empty={
                    !reports.data?.filter(
                      (r) =>
                        tab !== "Prescriptions" ||
                        r.category === "Prescriptions",
                    ).length
                  }
                  emptyTitle={"No shared " + tab.toLowerCase()}
                >
                  {reports.data
                    ?.filter(
                      (r) =>
                        tab !== "Prescriptions" ||
                        r.category === "Prescriptions",
                    )
                    .map((r) => (
                      <Link
                        className="dr-activity-row"
                        key={r.id}
                        to={`/doctor/reports?patient=${current.child_id}`}
                      >
                        <FileText size={18} />
                        <span>{r.name}</span>
                        <small>{r.created_at.slice(0, 10)}</small>
                      </Link>
                    ))}
                </PageStatus>
              )}
              <div className="dw-toolbar">
                <Link
                  className="dw-secondary"
                  to={"/doctor/patients/" + current.child_id}
                >
                  Open patient workspace
                </Link>
                <Link className="dw-secondary" to="/doctor/prescriptions">
                  Prescriptions
                </Link>
                <Link className="dw-secondary" to="/doctor/appointments">
                  Arrange follow-up
                </Link>
              </div>
            </section>
          )}
        </div>
      </PageStatus>
    </WorkspacePage>
  );
}
