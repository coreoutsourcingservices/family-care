import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Download, Eye, FileText, LayoutGrid, List } from "lucide-react";
import WorkspacePage, {
  useWorkspaceData,
  PageSearch,
  PageStatus,
} from "../components/WorkspacePage";
import PracticeChart from "../components/PracticeChart";
import {
  loadPatientRoster,
  loadVisibleReports,
  type SharedReport,
} from "../lib/workspaceApi";
import { downloadReport } from "../../../app/src/lib/healthProfiles";
import { ApiError } from "../../../app/src/lib/authApi";
type Report = SharedReport & { patientName: string };
const group = (r: SharedReport) =>
  /lab/i.test(r.category ?? "")
    ? "Lab Reports"
    : /scan|imag|x-ray/i.test(r.category ?? "")
      ? "Imaging Reports"
      : "Other Reports";
export default function Reports() {
  const [params] = useSearchParams();
  const [patient, setPatient] = useState(params.get("patient") ?? "all"),
    [search, setSearch] = useState(params.get("search") ?? ""),
    [fileType, setFileType] = useState("all"),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [sort, setSort] = useState("latest"),
    [grid, setGrid] = useState(false),
    [selected, setSelected] = useState(""),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [range, setRange] = useState(7);
  useEffect(() => setSearch(params.get("search") ?? ""), [params]);
  const state = useWorkspaceData("Reports:1", async () => {
    const patients = await loadPatientRoster();
    const reports: Report[] = [];
    let cursor = 0;
    await Promise.all(
      Array.from({ length: Math.min(4, patients.length) }, async () => {
        while (cursor < patients.length) {
          const p = patients[cursor++];
          try {
            const rows = await loadVisibleReports(p);
            reports.push(
              ...rows.map((r) => ({
                ...r,
                profile_id: p.id,
                patientName: p.full_name,
              })),
            );
          } catch (e) {
            if (e instanceof ApiError && e.status === 403) continue;
            throw e;
          }
        }
      }),
    );
    return { patients, reports };
  });
  const all = state.data?.reports ?? [];
  const rows = all
    .filter(
      (r) =>
        (patient === "all" || r.profile_id === patient) &&
        `${r.name} ${r.patientName} ${r.id}`
          .toLowerCase()
          .includes(search.toLowerCase()) &&
        (fileType === "all" ||
          (r.content_type?.startsWith("image/")
            ? "image"
            : r.content_type === "application/pdf" || /\.pdf$/i.test(r.name)
              ? "pdf"
              : "other") === fileType) &&
        (!start || r.created_at.slice(0, 10) >= start) &&
        (!end || r.created_at.slice(0, 10) <= end),
    )
    .sort((a, b) =>
      sort === "latest"
        ? b.created_at.localeCompare(a.created_at)
        : a.created_at.localeCompare(b.created_at),
    );
  const current = rows.find((r) => r.id === selected) ?? rows[0];
  const labels = ["Lab Reports", "Imaging Reports", "Other Reports"];
  const counts = labels.map((l) => rows.filter((r) => group(r) === l).length);
  const dates = Array.from({ length: range }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - range + 1 + i);
    return d.toLocaleDateString("en-CA");
  });
  async function open(r: Report) {
    setBusy(r.id);
    setError("");
    try {
      await downloadReport({
        id: r.id,
        name: r.name,
        addedAt: r.created_at,
        downloadPath:
          r.downloadPath ??
          `/api/v1/doctors/care-profiles/${r.profile_id}/reports/${r.id}/download`,
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <WorkspacePage
      title="Reports"
      description="View and manage shared patient reports."
      refresh={state.refresh}
    >
      <div className="dr-report-stats">
        {[
          ["Total Reports", all.length],
          ...labels.map((l) => [l, all.filter((r) => group(r) === l).length]),
        ].map(([label, n]) => (
          <article key={label}>
            <FileText />
            <div>
              <small>{label}</small>
              <strong>{state.loading ? "..." : state.error ? "--" : n}</strong>
            </div>
          </article>
        ))}
      </div>
      <div className="dw-toolbar">
        <select
          aria-label="Report patient"
          value={patient}
          onChange={(e) => setPatient(e.target.value)}
        >
          <option value="all">All Patients</option>
          {state.data?.patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.full_name}
            </option>
          ))}
        </select>
        <PageSearch
          value={search}
          onChange={setSearch}
          placeholder="Search reports, patient, or ID"
        />
        <select
          aria-label="Report file type"
          value={fileType}
          onChange={(e) => setFileType(e.target.value)}
        >
          <option value="all">All file types</option>
          <option value="pdf">PDF</option>
          <option value="image">Images</option>
          <option value="other">Other</option>
        </select>
        <label className="dr-date-filter">
          From
          <input
            type="date"
            aria-label="Reports from"
            value={start}
            max={end || undefined}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label className="dr-date-filter">
          To
          <input
            type="date"
            aria-label="Reports until"
            value={end}
            min={start || undefined}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
      </div>
      {error && (
        <p role="alert" className="dw-error">
          {error}
        </p>
      )}
      <PageStatus loading={state.loading} error={state.error}>
        <div className="dr-reports-layout">
          <div className="dr-report-main">
            <div className="dr-report-charts">
              <section className="dw-panel">
                <div className="dr-card-heading">
                  <div>
                    <h2>Reports Trend</h2>
                    <p>Shared reports uploaded over time.</p>
                  </div>
                  <select
                    aria-label="Report chart date range"
                    value={range}
                    onChange={(e) => setRange(Number(e.target.value))}
                  >
                    <option value={7}>Last 7 Days</option>
                    <option value={30}>Last 30 Days</option>
                  </select>
                </div>
                <PracticeChart
                  type="line"
                  label="Report uploads"
                  labels={dates.map((d) =>
                    new Date(d + "T00:00:00").toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                    }),
                  )}
                  values={dates.map(
                    (d) =>
                      rows.filter((r) => r.created_at.slice(0, 10) === d)
                        .length,
                  )}
                />
              </section>
              <section className="dw-panel">
                <h2>Reports by Category</h2>
                <div className="dr-report-category-chart">
                  <div className="dr-patient-donut">
                    <PracticeChart
                      type="doughnut"
                      label="Report categories"
                      labels={labels}
                      values={counts}
                    />
                    <div>
                      <strong>{rows.length}</strong>
                      <small>Reports</small>
                    </div>
                  </div>
                  <ul>
                    {labels.map((l, i) => (
                      <li key={l}>
                        <span>{l}</span>
                        <strong>{counts[i]}</strong>
                        <small>
                          {rows.length
                            ? ((counts[i] / rows.length) * 100).toFixed(1)
                            : 0}
                          %
                        </small>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>
            </div>
            <section className="dw-panel">
              <div className="dr-card-heading">
                <h2>Reports ({rows.length})</h2>
                <select
                  aria-label="Report sort order"
                  value={sort}
                  onChange={(e) => setSort(e.target.value)}
                >
                  <option value="latest">Latest First</option>
                  <option value="oldest">Oldest First</option>
                </select>
                <button
                  className="dr-icon-button"
                  aria-label={grid ? "Show report list" : "Show report grid"}
                  onClick={() => setGrid(!grid)}
                >
                  {grid ? <List size={18} /> : <LayoutGrid size={18} />}
                </button>
              </div>
              <PageStatus
                loading={false}
                error=""
                empty={!rows.length}
                emptyTitle="No matching reports"
              >
                {grid ? (
                  <div className="dr-report-file-grid">
                    {rows.map((r) => (
                      <button
                        className="dr-report-file"
                        key={r.id}
                        onClick={() => setSelected(r.id)}
                      >
                        <FileText />
                        <strong>{r.name}</strong>
                        <small>{r.patientName}</small>
                        <span>{r.created_at.slice(0, 10)}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="dw-table-wrap">
                    <table className="dw-table">
                      <thead>
                        <tr>
                          <th>Patient</th>
                          <th>Report Name</th>
                          <th>Category</th>
                          <th>Uploaded</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r) => (
                          <tr
                            key={r.id}
                            className={
                              current?.id === r.id ? "dr-selected-row" : ""
                            }
                          >
                            <td data-label="Patient">
                              <button
                                className="dr-text-button"
                                onClick={() => setSelected(r.id)}
                              >
                                {r.patientName}
                              </button>
                            </td>
                            <td data-label="Report">
                              <button
                                className="dr-text-button"
                                onClick={() => setSelected(r.id)}
                              >
                                {r.name}
                              </button>
                            </td>
                            <td data-label="Category">
                              <span className="dw-badge">
                                {r.category || "Uncategorized"}
                              </span>
                            </td>
                            <td data-label="Uploaded">
                              {r.created_at.slice(0, 10)}
                            </td>
                            <td data-label="Status">
                              {r.category_reviewed ? "Categorized" : "Shared"}
                            </td>
                            <td data-label="Actions">
                              <div className="dr-report-actions">
                                <button
                                  aria-label={"View details " + r.name}
                                  onClick={() => setSelected(r.id)}
                                >
                                  <Eye size={16} />
                                </button>
                                <button
                                  disabled={!!busy}
                                  aria-label={"Download " + r.name}
                                  onClick={() => void open(r)}
                                >
                                  <Download size={16} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </PageStatus>
            </section>
            {current && (
              <section className="dw-panel dr-report-detail">
                <div className="dr-card-heading">
                  <FileText className="dr-blue" />
                  <div>
                    <h2>{current.name}</h2>
                    <p>
                      {group(current)} / {current.patientName}
                    </p>
                  </div>
                  <button
                    className="button primary"
                    disabled={!!busy}
                    onClick={() => void open(current)}
                  >
                    <Download size={16} />
                    {busy ? "Opening..." : "Open / Download"}
                  </button>
                </div>
                <div className="dr-report-detail-grid">
                  <article>
                    <h3>Report Details</h3>
                    <dl>
                      <dt>Uploaded</dt>
                      <dd>
                        {new Date(current.created_at).toLocaleString("en-IN")}
                      </dd>
                      <dt>Patient</dt>
                      <dd>{current.patientName}</dd>
                      <dt>File size</dt>
                      <dd>
                        {current.size_bytes !== undefined
                          ? Math.ceil(current.size_bytes / 1024) + " KB"
                          : "Not provided"}
                      </dd>
                      <dt>File type</dt>
                      <dd>{current.content_type || "Document"}</dd>
                    </dl>
                  </article>
                  <article>
                    <h3>Document overview</h3>
                    <p>{current.category || "Category not yet set"}</p>
                    <p>Open the original report to review the findings.</p>
                    <Link
                      className="dw-secondary"
                      to={"/doctor/patients/" + current.profile_id}
                    >
                      View Patient
                    </Link>
                  </article>
                </div>
              </section>
            )}
          </div>
          <aside className="dr-report-side">
            <section className="dw-panel">
              <h2>Recent Uploads</h2>
              {[...rows]
                .sort((a, b) => b.created_at.localeCompare(a.created_at))
                .slice(0, 3)
                .map((r) => (
                  <button
                    className="dr-recent-file"
                    key={r.id}
                    onClick={() => setSelected(r.id)}
                  >
                    <FileText size={19} />
                    <span>
                      <strong>{r.name}</strong>
                      <small>
                        {r.patientName} / {r.created_at.slice(0, 10)}
                      </small>
                    </span>
                  </button>
                ))}
              {!rows.length && (
                <p className="dr-empty">No uploads in this view.</p>
              )}
            </section>
            <section className="dw-panel">
              <h2>Report Categories</h2>
              {labels.map((l, i) => (
                <div className="dr-category-bar" key={l}>
                  <span>{l}</span>
                  <strong>{counts[i]}</strong>
                  <div>
                    <i
                      style={{
                        width:
                          (rows.length ? (counts[i] / rows.length) * 100 : 0) +
                          "%",
                        background: ["#8060ff", "#2488ff", "#12c5b5"][i],
                      }}
                    />
                  </div>
                </div>
              ))}
            </section>
          </aside>
        </div>
      </PageStatus>
    </WorkspacePage>
  );
}
