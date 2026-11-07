import AgentBentoGrid, { FeatCard } from "../components/AgentBentoGrid";
import PracticeChart from "../components/PracticeChart";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Download, FileText, Activity, Users } from "lucide-react";
import WorkspacePage, {
  PageSearch,
  PageStatus,
  useWorkspaceData,
} from "../components/WorkspacePage";
import { PatientName, RowActions } from "../components/TableElements";
import {
  loadPatientRoster,
  loadVisibleRecords,
  loadReports,
} from "../lib/workspaceApi";
import { downloadReport } from "../../../app/src/lib/healthProfiles";

export default function SharedPatientPage({
  mode,
}: {
  mode: "records" | "reports" | "prescriptions";
}) {
  const [params, setParams] = useSearchParams();
  const patients = useWorkspaceData("SharedPatientPage:1", loadPatientRoster);
  const patientId = params.get("patient") ?? "";
  const allowed =
    patients.data?.some((patient) => patient.id === patientId) ?? false;
  const [search, setSearch] = useState(params.get("search") ?? "");
  useEffect(() => setSearch(params.get("search") ?? ""), [params]);
  const [type, setType] = useState("all");
  const [range, setRange] = useState("all");
  const [downloadError, setDownloadError] = useState("");
  const [downloading, setDownloading] = useState("");
  useEffect(() => {
    if (patients.data?.length && !allowed) {
      const next = new URLSearchParams(params);
      next.set("patient", patients.data[0].id);
      setParams(next, { replace: true });
    }
  }, [patients.data, allowed, setParams]);
  const records = useWorkspaceData("SharedPatientPage:2",
    () =>
      allowed && mode === "records"
        ? loadVisibleRecords(patients.data!.find((p) => p.id === patientId)!)
        : Promise.resolve([]),
    [allowed, patientId, mode],
  );
  const reports = useWorkspaceData("SharedPatientPage:3",
    () =>
      allowed && mode !== "records"
        ? loadReports(patientId)
        : Promise.resolve([]),
    [allowed, patientId, mode],
  );
  const title =
    mode === "records"
      ? "Clinical Records"
      : mode === "reports"
        ? "Reports"
        : "Prescriptions";
  const state = mode === "records" ? records : reports;
  const recordRows =
    records.data?.filter(
      (row) =>
        (type === "all" || row.kind === type) &&
        `${row.title} ${row.kind} ${row.notes ?? ""}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    ) ?? [];
  const reportRows =
    reports.data?.filter(
      (row) =>
        (mode !== "prescriptions" || row.category === "Prescriptions") &&
        (type === "all" ||
          (row.content_type?.startsWith("image/") ||
          /\.(png|jpe?g|webp)$/i.test(row.name)
            ? "image"
            : /\.pdf$/i.test(row.name)
              ? "pdf"
              : "document") === type) &&
        (range === "all" ||
          Date.now() - Date.parse(row.created_at) <=
            Number(range) * 86400000) &&
        row.name.toLowerCase().includes(search.toLowerCase()),
    ) ?? [];
  const selectedName =
    patients.data?.find((patient) => patient.id === patientId)?.full_name ??
    "Shared profile";
  return (
    <WorkspacePage
      title={title}
      description={
        mode === "records"
          ? "Review family-reported clinical history shared with your practice."
          : "View original documents shared by connected families."
      }
      refresh={() => {
        patients.refresh();
        records.refresh();
        reports.refresh();
      }}
    >
      {mode !== "records" && (
        <div className="dr-report-stats">
          {[
            ["Total Reports", reports.data?.length ?? 0],
            [
              "Lab Reports",
              reports.data?.filter((r) => r.category === "Lab tests").length ??
                0,
            ],
            [
              "Imaging Reports",
              reports.data?.filter((r) => r.category === "Scans").length ?? 0,
            ],
            [
              "Other Reports",
              reports.data?.filter(
                (r) => !["Lab tests", "Scans"].includes(r.category ?? ""),
              ).length ?? 0,
            ],
          ].map(([label, count]) => (
            <article key={label}>
              <FileText />
              <div>
                <small>{label}</small>
                <strong>{state.loading ? "..." : count}</strong>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className={mode === "records" ? "dr-record-layout" : ""}>
        {mode === "records" && (
          <aside className="dw-panel dr-record-patients">
            <h3>Connected patients</h3>
            {patients.data?.map((p) => (
              <Link
                className={p.id === patientId ? "active" : ""}
                key={p.id}
                to={"/doctor/clinical-records?patient=" + p.id}
              >
                <Users size={16} />
                {p.full_name}
              </Link>
            ))}
          </aside>
        )}
        <div>
          <div className="dw-toolbar">
            <select
              aria-label="Select patient"
              disabled={!patients.data?.length}
              value={allowed ? patientId : ""}
              onChange={(event) => {
                setParams({ patient: event.target.value });
                setSearch("");
                setDownloadError("");
              }}
            >
              <option value="" disabled>
                Select a patient
              </option>
              {patients.data?.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.full_name}
                </option>
              ))}
            </select>
            <PageSearch
              value={search}
              onChange={setSearch}
              placeholder={`Search ${title.toLowerCase()}`}
            />
            <select
              aria-label={mode === "records" ? "Record type" : "Report type"}
              value={type}
              onChange={(event) => setType(event.target.value)}
            >
              <option value="all">
                {mode === "records" ? "All record types" : "All file types"}
              </option>
              {mode === "records" ? (
                [...new Set(records.data?.map((row) => row.kind))].map(
                  (kind) => (
                    <option key={kind} value={kind}>
                      {kind.replaceAll("_", " ")}
                    </option>
                  ),
                )
              ) : (
                <>
                  <option value="pdf">PDF</option>
                  <option value="image">Image</option>
                  <option value="document">Other documents</option>
                </>
              )}
            </select>
            {mode !== "records" && (
              <select
                aria-label="Shared date range"
                value={range}
                onChange={(event) => setRange(event.target.value)}
              >
                <option value="all">All time</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
            )}
          </div>
          {mode === "records" && (
            <p className="dw-info">
              Entries are family-reported history. They are not doctor-authored
              diagnoses or prescriptions.
            </p>
          )}
          {mode === "prescriptions" && (
            <p className="dw-info">
              Only documents explicitly categorized as Prescriptions appear
              here. Uploaded files are separate from doctor-issued
              prescriptions.{" "}
              <Link to={`/doctor/reports?patient=${patientId}`}>
                Browse all shared reports
              </Link>
              .
            </p>
          )}
          {downloadError && (
            <p className="dw-error" role="alert">
              {downloadError}
            </p>
          )}
          {mode === "records" &&
            allowed &&
            !records.loading &&
            !records.error && (
              <AgentBentoGrid>
                <FeatCard
                  title="Record Types"
                  description="Shared records by category"
                  tone="cyan"
                >
                  <PracticeChart
                    type="doughnut"
                    label="Clinical record types"
                    showLegend
                    labels={[...new Set(recordRows.map((r) => r.kind))]}
                    values={[...new Set(recordRows.map((r) => r.kind))].map(
                      (k) => recordRows.filter((r) => r.kind === k).length,
                    )}
                  />
                </FeatCard>
                <FeatCard
                  title="Health Timeline"
                  description="Recorded entries across the last 6 months"
                  tone="violet"
                >
                  <PracticeChart
                    type="bar"
                    label="Clinical record activity"
                    labels={Array.from({ length: 6 }, (_, i) =>
                      new Date(
                        new Date().getFullYear(),
                        new Date().getMonth() - 5 + i,
                        1,
                      ).toLocaleDateString("en-IN", { month: "short" }),
                    )}
                    values={Array.from({ length: 6 }, (_, i) => {
                      const d = new Date(
                        new Date().getFullYear(),
                        new Date().getMonth() - 5 + i,
                        1,
                      );
                      return recordRows.filter(
                        (r) =>
                          r.date.slice(0, 7) ===
                          `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
                      ).length;
                    })}
                  />
                </FeatCard>
              </AgentBentoGrid>
            )}
          <PageStatus
            loading={patients.loading || (allowed && state.loading)}
            error={patients.error || state.error}
            empty={
              !allowed ||
              (mode === "records" ? !recordRows.length : !reportRows.length)
            }
            emptyTitle={
              !patients.data?.length
                ? "No connected patient profiles"
                : `No matching ${title.toLowerCase()}`
            }
          >
            {mode === "records" ? (
              <section className="dw-panel">
                <div className="dr-card-heading">
                  <span className="dr-avatar">{selectedName.charAt(0)}</span>
                  <div>
                    <h2>{selectedName}</h2>
                    <p>Shared clinical history</p>
                  </div>
                  <Link
                    className="dw-secondary"
                    to={"/doctor/patients/" + patientId}
                  >
                    Patient overview
                  </Link>
                </div>
                <h3>Health Timeline</h3>
                <div className="dr-health-timeline">
                  {recordRows.map((row) => (
                    <article key={row.id}>
                      <span className="dr-timeline-icon">
                        <Activity size={19} />
                      </span>
                      <div>
                        <time>{row.date}</time>
                        <h3>{row.title}</h3>
                        <p>{row.notes || "No additional notes recorded."}</p>
                        <div className="dr-timeline-values">
                          {row.weight && <span>Weight: {row.weight} kg</span>}
                          {row.height && <span>Height: {row.height} cm</span>}
                          {row.systolic != null && (
                            <span>
                              BP: {row.systolic}/{row.diastolic} mmHg
                            </span>
                          )}
                          {row.glucose != null && (
                            <span>Glucose: {row.glucose} mg/dL</span>
                          )}
                          {row.pulse != null && (
                            <span>Pulse: {row.pulse} bpm</span>
                          )}
                          {(
                            ["total", "ldl", "hdl", "triglycerides"] as const
                          ).map(
                            (key) =>
                              row[key] != null && (
                                <span key={key}>
                                  {key.toUpperCase()}: {row[key]} mg/dL
                                </span>
                              ),
                          )}
                          {row.minutes != null && (
                            <span>Activity: {row.minutes} min</span>
                          )}
                          {row.context && <span>{row.context}</span>}
                        </div>
                        <small>
                          {row.source_role === "DOCTOR"
                            ? "Doctor reported"
                            : "Family reported"}
                        </small>
                      </div>
                      <span className="dw-badge">
                        {row.kind.replaceAll("_", " ")}
                      </span>
                    </article>
                  ))}
                </div>
              </section>
            ) : (
              <div className="dw-panel dw-table-wrap">
                <table className="dw-table">
                  <thead>
                    <tr>
                      <th>Patient</th>
                      <th>
                        {mode === "prescriptions" ? "File name" : "Report name"}
                      </th>
                      <th>Type</th>
                      <th>Shared on</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportRows.map((report) => (
                      <tr key={report.id}>
                        <td>
                          <PatientName name={selectedName} />
                        </td>
                        <td>
                          <h3 className="dw-row-title">{report.name}</h3>
                          {report.size_bytes !== undefined && (
                            <small>
                              {Math.ceil(report.size_bytes / 1024)} KB
                            </small>
                          )}
                        </td>
                        <td>
                          <span className="dw-badge">
                            {mode === "prescriptions"
                              ? "Prescription file"
                              : report.content_type?.startsWith("image/") ||
                                  /\.(png|jpe?g|webp)$/i.test(report.name)
                                ? "Image"
                                : /\.pdf$/i.test(report.name)
                                  ? "PDF document"
                                  : "Document"}
                          </span>
                        </td>
                        <td>
                          <time>{report.created_at.slice(0, 10)}</time>
                        </td>
                        <td>
                          <RowActions label={report.name}>
                            <button
                              className="dw-secondary"
                              disabled={!!downloading}
                              onClick={async () => {
                                setDownloading(report.id);
                                setDownloadError("");
                                try {
                                  await downloadReport({
                                    id: report.id,
                                    name: report.name,
                                    addedAt: report.created_at,
                                    downloadPath: `/api/v1/doctors/care-profiles/${patientId}/reports/${report.id}/download`,
                                  });
                                } catch (error) {
                                  setDownloadError(
                                    error instanceof Error
                                      ? error.message
                                      : "Could not open this report.",
                                  );
                                } finally {
                                  setDownloading("");
                                }
                              }}
                            >
                              <Download size={15} />
                              {downloading === report.id
                                ? "Opening..."
                                : "Open original"}
                            </button>
                          </RowActions>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </PageStatus>
        </div>
      </div>
    </WorkspacePage>
  );
}
