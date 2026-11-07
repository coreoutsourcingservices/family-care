import AgentBentoGrid, { FeatCard } from "../components/AgentBentoGrid";
import PracticeChart from "../components/PracticeChart";
import { useEffect, useState, type FormEvent } from "react";
import WorkspacePage, {
  useWorkspaceData,
  PageStatus,
  PageSearch,
} from "../components/WorkspacePage";
import { FileText, Pill, CalendarDays, Printer } from "lucide-react";
import { careApi, loadPatients } from "../lib/workspaceApi";
type Rx = {
  id: string;
  status: string;
  version: number;
  doctor_name: string;
  issued_at: string | null;
  void_reason?: string;
  data: {
    medicines: {
      name: string;
      strength: string;
      dose: string;
      frequency: string;
      duration: string;
      instructions: string;
    }[];
    instructions: string;
    follow_up?: string;
    issuer?: { name: string; registration: string };
  };
};
export default function Prescriptions() {
  const patients = useWorkspaceData("Prescriptions:1", async () => {
      const [regular, women, adult] = await Promise.all([
        loadPatients(),
        careApi<{
          items: {
            id: string;
            name: string;
            permissions: Record<string, string>;
          }[];
        }>("/women/shared"),
        careApi<{
          items: {
            id: string;
            name: string;
            permissions: Record<string, string>;
          }[];
        }>("/adult-access/shared"),
      ]);
      return Array.from(
        new Map(
          [
            ...regular
              .filter((p) => p.module === "child")
              .map((p) => ({ ...p, can_prescribe: true })),
            ...women.items
              .filter((p) => p.permissions.records)
              .map((p) => ({
                id: p.id,
                full_name: p.name,
                module: "women",
                can_prescribe: p.permissions.records === "edit",
              })),
            ...adult.items
              .filter((p) => p.permissions.reports)
              .map((p) => ({
                id: p.id,
                full_name: p.name,
                module: "adult",
                can_prescribe: p.permissions.reports === "edit",
              })),
          ].map((p) => [p.id, p]),
        ).values(),
      );
    }),
    [patient, setPatient] = useState(""),
    [draft, setDraft] = useState<Rx>(),
    [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [count, setCount] = useState(1);
  useEffect(() => {
    if (!patient && patients.data?.length) setPatient(patients.data[0].id);
  }, [patient, patients.data]);
  const allowed = patients.data?.some((p) => p.id === patient);
  const editable = patients.data?.find((p) => p.id === patient)?.can_prescribe;
  const rows = useWorkspaceData("Prescriptions:2",
    async () =>
      allowed
        ? (
            await careApi<{ items: Rx[] }>(
              `/doctors/care-profiles/${patient}/prescriptions`,
            )
          ).items
        : [],
    [patient, allowed],
  );
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const medicines = Array.from({ length: count }, (_, i) =>
        Object.fromEntries(
          [
            "name",
            "strength",
            "dose",
            "frequency",
            "duration",
            "instructions",
          ].map((k) => [k, form.get(k + i) || ""]),
        ),
      );
      await careApi(
        `/doctors/care-profiles/${patient}/prescriptions${draft ? "/" + draft.id : ""}`,
        {
          medicines,
          instructions: form.get("instructions"),
          follow_up: form.get("follow_up") || null,
          version: draft?.version ?? 0,
        },
        true,
        draft ? "PUT" : "POST",
      );
      setOpen(false);
      rows.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function decide(row: Rx, action: "ISSUE" | "VOID") {
    const reason =
      action === "VOID"
        ? window.prompt("Reason for voiding this prescription?")
        : "";
    if (action === "VOID" && !reason?.trim()) return;
    if (
      !window.confirm(
        action === "ISSUE"
          ? "I have reviewed the patient, medicines, doses and instructions. Issue with my name and registration? Issued content cannot be edited."
          : "Void this prescription? It stays in history with your reason.",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      await careApi(
        `/doctors/care-profiles/${patient}/prescriptions/${row.id}/decision`,
        {
          action,
          version: row.version,
          attestation: true,
          reason: reason || "",
        },
      );
      rows.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all"),
    [selectedId, setSelectedId] = useState("");
  const filtered = (rows.data ?? []).filter(
    (r) =>
      (filter === "all" || r.status === filter) &&
      JSON.stringify(r.data).toLowerCase().includes(search.toLowerCase()),
  );
  const selected = filtered.find((r) => r.id === selectedId) ?? filtered[0];
  const person = patients.data?.find((p) => p.id === patient);
  function edit(row: Rx) {
    setDraft(row);
    setCount(row.data.medicines.length);
    setOpen(true);
  }
  return (
    <WorkspacePage
      title="Prescriptions"
      description="Create, review and issue prescriptions for authorized patients."
      refresh={rows.refresh}
    >
      <div className="dr-report-stats dr-rx-stats">
        {[
          ["Total Prescriptions", rows.data?.length ?? 0],
          [
            "Drafts",
            rows.data?.filter((r) => r.status === "DRAFT").length ?? 0,
          ],
          [
            "Issued",
            rows.data?.filter((r) => r.status === "ISSUED").length ?? 0,
          ],
          [
            "Issued in Last 7 Days",
            rows.data?.filter(
              (r) =>
                r.status === "ISSUED" &&
                r.issued_at &&
                Date.now() - Date.parse(r.issued_at) <= 7 * 86400000,
            ).length ?? 0,
          ],
        ].map(([label, value]) => (
          <article key={label}>
            <FileText />
            <div>
              <small>{label}</small>
              <strong>{rows.loading ? "..." : value}</strong>
            </div>
          </article>
        ))}
      </div>
      <div className="dw-toolbar">
        <select
          aria-label="Select prescription patient"
          value={patient}
          disabled={busy}
          onChange={(e) => {
            setPatient(e.target.value);
            setOpen(false);
            setError("");
            setSelectedId("");
          }}
        >
          <option value="">Select patient</option>
          {patients.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.full_name} / {p.module}
            </option>
          ))}
        </select>
        <PageSearch
          value={search}
          onChange={setSearch}
          placeholder="Search prescriptions or medicines"
        />
        <button
          className="button primary"
          disabled={!allowed || !editable || busy}
          onClick={() => {
            setDraft(undefined);
            setCount(1);
            setOpen(true);
          }}
        >
          + New Prescription
        </button>
      </div>
      {error && (
        <p className="dw-error" role="alert">
          {error}
        </p>
      )}
      {allowed && !rows.loading && !rows.error && (
        <AgentBentoGrid>
          <FeatCard
            title="Prescription Status"
            description="Draft, issued and voided prescriptions"
            tone="violet"
          >
            <PracticeChart
              type="doughnut"
              label="Prescription status"
              showLegend
              labels={["Draft", "Issued", "Voided"]}
              values={["DRAFT", "ISSUED", "VOID"].map(
                (k) => rows.data?.filter((r) => r.status === k).length ?? 0,
              )}
            />
          </FeatCard>
          <FeatCard
            title="Issuing Activity"
            description="Prescriptions issued over the last 7 days"
            tone="mint"
          >
            <PracticeChart
              type="bar"
              label="Prescription issuing activity"
              labels={Array.from({ length: 7 }, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - 6 + i);
                return d.toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                });
              })}
              values={Array.from({ length: 7 }, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - 6 + i);
                return (
                  rows.data?.filter(
                    (r) =>
                      r.issued_at &&
                      new Date(r.issued_at).toLocaleDateString("en-CA") ===
                        d.toLocaleDateString("en-CA"),
                  ).length ?? 0
                );
              })}
            />
          </FeatCard>
        </AgentBentoGrid>
      )}
      <div className="dr-rx-layout">
        <section className="dw-panel dr-rx-list">
          <h2>
            Prescriptions <small>({filtered.length})</small>
          </h2>
          <div className="dr-tabs">
            {["all", "DRAFT", "ISSUED", "VOID"].map((t) => (
              <button
                className={filter === t ? "active" : ""}
                key={t}
                onClick={() => setFilter(t)}
              >
                {t === "all"
                  ? "All"
                  : t === "VOID"
                    ? "Voided"
                    : t.charAt(0) + t.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
          <PageStatus
            loading={patients.loading || rows.loading}
            error={patients.error || rows.error}
            empty={!allowed || !filtered.length}
            emptyTitle={
              allowed
                ? "No matching prescriptions"
                : "Select an authorized patient"
            }
          >
            {filtered.map((row) => (
              <button
                className={
                  "dr-rx-item " + (selected?.id === row.id ? "active" : "")
                }
                key={row.id}
                onClick={() => {
                  setSelectedId(row.id);
                  setOpen(false);
                }}
              >
                <span className="dr-avatar">{person?.full_name.charAt(0)}</span>
                <span>
                  <strong>{person?.full_name}</strong>
                  <small>
                    {row.data.medicines.map((m) => m.name).join(", ")}
                  </small>
                </span>
                <span className="dw-badge">{row.status}</span>
              </button>
            ))}
          </PageStatus>
        </section>
        <section className="dw-panel dr-rx-detail">
          {open ? (
            <form
              className="prescription-editor"
              key={draft?.id || "new"}
              onSubmit={save}
            >
              <h2>{draft ? "Edit draft" : "New prescription draft"}</h2>
              <p>{person?.full_name}</p>
              <fieldset disabled={busy}>
                {Array.from({ length: count }, (_, index) => (
                  <fieldset className="clinical-form-grid" key={index}>
                    <legend>Medicine {index + 1}</legend>
                    {(
                      [
                        "name",
                        "strength",
                        "dose",
                        "frequency",
                        "duration",
                        "instructions",
                      ] as const
                    ).map((key) => (
                      <label key={key}>
                        {key}
                        <input
                          name={key + index}
                          defaultValue={
                            draft?.data.medicines[index]?.[key] || ""
                          }
                          required={key !== "instructions"}
                          maxLength={key === "instructions" ? 500 : 120}
                        />
                      </label>
                    ))}
                  </fieldset>
                ))}
                <button
                  type="button"
                  className="dw-secondary"
                  disabled={count >= 30}
                  onClick={() => setCount((c) => c + 1)}
                >
                  + Add medicine
                </button>
                <label>
                  Prescriber instructions
                  <textarea
                    name="instructions"
                    maxLength={3000}
                    defaultValue={draft?.data.instructions}
                  />
                </label>
                <label>
                  Follow-up date
                  <input
                    type="date"
                    name="follow_up"
                    defaultValue={draft?.data.follow_up || ""}
                  />
                </label>
                <div className="dw-toolbar">
                  <button className="button primary">
                    Save draft for review
                  </button>
                  <button
                    type="button"
                    className="dw-secondary"
                    onClick={() => setOpen(false)}
                  >
                    Cancel
                  </button>
                </div>
              </fieldset>
            </form>
          ) : selected ? (
            <>
              <div className="dr-card-heading">
                <span className="dr-avatar">{person?.full_name.charAt(0)}</span>
                <div>
                  <h2>{person?.full_name}</h2>
                  <p>Patient ID: {patient}</p>
                </div>
                <span className="dw-badge">{selected.status}</span>
              </div>
              <div className="dr-rx-reason">
                <Pill size={20} />
                <div>
                  <h3>Prescription details</h3>
                  <p>
                    {selected.doctor_name}
                    {selected.data.issuer
                      ? " / Registration: " + selected.data.issuer.registration
                      : ""}
                  </p>
                </div>
              </div>
              <div className="dr-card-heading">
                <h3>
                  Prescribed Medications ({selected.data.medicines.length})
                </h3>
                {selected.status === "DRAFT" && editable && (
                  <button
                    className="dw-secondary"
                    disabled={busy}
                    onClick={() => edit(selected)}
                  >
                    Edit medications
                  </button>
                )}
              </div>
              <div className="dw-table-wrap">
                <table className="dw-table">
                  <thead>
                    <tr>
                      <th>Medicine</th>
                      <th>Dosage</th>
                      <th>Frequency</th>
                      <th>Duration</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.data.medicines.map((m, i) => (
                      <tr key={i}>
                        <td data-label="Medicine">
                          <strong>{m.name}</strong>
                          <small>{m.strength}</small>
                        </td>
                        <td data-label="Dose">{m.dose}</td>
                        <td data-label="Frequency">{m.frequency}</td>
                        <td data-label="Duration">{m.duration}</td>
                        <td data-label="Notes">{m.instructions || "--"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <section className="dr-rx-notes">
                <h3>Prescriber Notes</h3>
                <p>
                  {selected.data.instructions ||
                    "No additional instructions recorded."}
                </p>
              </section>
              <section className="dr-rx-activity">
                <h3>
                  <CalendarDays size={18} />
                  Prescription Activity
                </h3>
                <p>
                  <strong>
                    {selected.status === "DRAFT"
                      ? "Draft - not issued"
                      : selected.status === "VOID"
                        ? "Voided"
                        : "Issued"}
                  </strong>
                  {selected.issued_at && (
                    <time>
                      {new Date(selected.issued_at).toLocaleString("en-IN")}
                    </time>
                  )}
                </p>
                {selected.data.follow_up && (
                  <p>
                    Follow-up date <time>{selected.data.follow_up}</time>
                  </p>
                )}
                {selected.void_reason && (
                  <p>Void reason: {selected.void_reason}</p>
                )}
              </section>
              <div className="dw-toolbar">
                {selected.status === "DRAFT" ? (
                  <>
                    <button
                      className="dw-secondary"
                      disabled={busy || !editable}
                      onClick={() => edit(selected)}
                    >
                      Edit Draft
                    </button>
                    <button
                      className="button primary"
                      disabled={busy || !editable}
                      onClick={() => void decide(selected, "ISSUE")}
                    >
                      Review &amp; Issue Prescription
                    </button>
                  </>
                ) : (
                  selected.status === "ISSUED" && (
                    <button
                      className="dw-secondary"
                      disabled={busy || !editable}
                      onClick={() => void decide(selected, "VOID")}
                    >
                      Void with reason
                    </button>
                  )
                )}
                <button className="dw-secondary" onClick={() => window.print()}>
                  <Printer size={16} />
                  Print
                </button>
              </div>
            </>
          ) : (
            <div className="dr-empty">
              Choose a prescription or create a new draft.
            </div>
          )}
        </section>
      </div>
    </WorkspacePage>
  );
}
