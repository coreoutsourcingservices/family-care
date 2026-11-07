import { DoctorReferralConsent } from "./DoctorHandoffs";
import { useEffect, useState, type FormEvent } from "react";
import {
  ShieldCheck,
  Share2,
  Clock3,
  History,
  Stethoscope,
  Users,
  Heart,
  FileText,
  Activity,
  CalendarDays,
  LockKeyhole,
  Check,
  X,
} from "lucide-react";
import { careApi } from "../lib/careApi";
import "./health-sharing.css";
type Grant = {
  id: string;
  recipient_id: string;
  name: string;
  role: string;
  permissions: Record<string, "view" | "edit">;
  active: boolean;
  starts_at: string | null;
  expires_at: string | null;
  revoked_at?: string | null;
};
type Sharing = {
  tabs: Record<string, string>;
  recipients: { id: string; name: string; role: string }[];
  grants: Grant[];
};
type AccessEvent = {
  id: string;
  action: string;
  name: string;
  permissions: Record<string, string>;
  created_at: string;
};
const icons = [
  Heart,
  CalendarDays,
  Activity,
  Heart,
  Activity,
  Heart,
  Activity,
  FileText,
  Stethoscope,
  ShieldCheck,
];
export default function HealthSharing({
  profileId,
  module,
}: {
  profileId: string;
  module: "adult" | "women";
}) {
  const [data, setData] = useState<Sharing>(),
    [panel, setPanel] = useState("share"),
    [role, setRole] = useState("DOCTOR"),
    [recipient, setRecipient] = useState(""),
    [code, setCode] = useState(""),
    [permissions, setPermissions] = useState<Record<string, "view" | "edit">>(
      {},
    ),
    [duration, setDuration] = useState("unlimited"),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [events, setEvents] = useState<AccessEvent[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const base = `/${module === "women" ? "women" : "adult-access"}/profiles/${profileId}`,
    path = base + "/sharing";
  async function load() {
    const result = await careApi<Sharing>(path);
    setData(result);
    return result;
  }
  useEffect(() => {
    setData(undefined);
    setError("");
    setRecipient("");
    setPermissions({});
    setDuration("unlimited");
    void load().catch((e) => setError(e.message));
  }, [path]);
  useEffect(() => {
    if (panel === "history")
      careApi<{ items: AccessEvent[] }>(base + "/history")
        .then((d) => setEvents(d.items))
        .catch((e) => setError(e.message));
  }, [panel, base]);
  const tabs = Object.entries(data?.tabs ?? {}),
    recipients = data?.recipients.filter((r) => r.role === role) ?? [];
  function select(id: string) {
    setRecipient(id);
    const grant = data?.grants.find(
      (g) => g.recipient_id === id && !g.revoked_at,
    );
    setPermissions(grant?.permissions ?? {});
    setDuration(grant?.expires_at ? "custom" : "unlimited");
    setStart(grant?.starts_at ? local(grant.starts_at) : "");
    setEnd(grant?.expires_at ? local(grant.expires_at) : "");
    setNotice("");
  }
  function local(value: string) {
    const d = new Date(value);
    return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const expires =
        duration === "unlimited"
          ? null
          : duration === "custom"
            ? new Date(end).toISOString()
            : new Date(Date.now() + Number(duration) * 86400000).toISOString();
      await careApi(
        path,
        {
          recipient_id: recipient,
          permissions,
          starts_at:
            duration === "custom" && start
              ? new Date(start).toISOString()
              : null,
          expires_at: expires,
        },
        true,
        "PUT",
      );
      await load();
      setNotice("Access saved. Only selected tabs are shared.");
      setPanel("manage");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className={"hs-page hs-" + module}
      aria-label={
        module === "women" ? "Women tab sharing" : "Adult tab sharing"
      }
    >
      <header className="hs-hero">
        <span className="hs-hero-icon">
          <ShieldCheck />
        </span>
        <div>
          <h1>Access & Sharing</h1>
          <p>
            Choose who can view or edit your health records. Change or revoke
            access anytime.
          </p>
        </div>
        <LockKeyhole className="hs-hero-art" />
      </header>
      <nav className="hs-nav" aria-label="Access panels">
        {[
          ["share", "Share Access", Share2],
          ["manage", "Manage Access", Clock3],
          ["history", "Access History", History],
        ].map(([id, label, Icon]) => {
          const I = Icon as typeof Share2;
          return (
            <button
              type="button"
              key={id as string}
              className={panel === id ? "active" : ""}
              onClick={() => {
                setPanel(id as string);
                setError("");
              }}
            >
              <I size={19} />
              {label as string}
            </button>
          );
        })}
      </nav>
      {error && (
        <p className="hs-error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="hs-notice" role="status">
          <Check size={16} />
          {notice}
        </p>
      )}
      {module === "women" && <DoctorReferralConsent profileId={profileId} />}{" "}
      {panel === "share" ? (
        <form onSubmit={save}>
          <fieldset disabled={busy}>
            <section className="hs-section">
              <h2>
                <b>1</b>Choose who to share with
              </h2>
              <div className="hs-roles">
                {[
                  [
                    "DOCTOR",
                    "Doctor",
                    "Share selected tabs with your connected doctor.",
                    Stethoscope,
                  ],
                  [
                    "PATIENT",
                    "Family member",
                    "Allow a family member to view selected records.",
                    Users,
                  ],
                ].map(([id, label, copy, Icon]) => {
                  const I = Icon as typeof Heart;
                  return (
                    <button
                      type="button"
                      className={role === id ? "selected" : ""}
                      key={id as string}
                      onClick={() => {
                        setRole(id as string);
                        setRecipient("");
                        setPermissions({});
                        setDuration("unlimited");
                      }}
                    >
                      <I />
                      <span>
                        <strong>{label as string}</strong>
                        <small>{copy as string}</small>
                      </span>
                      <span className="hs-radio">
                        {role === id ? "●" : "○"}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="hs-connect">
                {role === "DOCTOR" && (
                  <>
                    <label>
                      Doctor referral ID / code
                      <input
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        placeholder="Enter doctor referral ID"
                        maxLength={160}
                      />
                    </label>
                    <button
                      type="button"
                      className="hs-secondary"
                      disabled={!code.trim()}
                      onClick={async () => {
                        setBusy(true);
                        setError("");
                        try {
                          await careApi(
                            "/patients/profiles/" +
                              profileId +
                              "/connect-doctor",
                            { referral_id: code.trim() },
                          );
                          const result = await load();
                          const doctor = result.recipients.find(
                            (r) => r.role === "DOCTOR",
                          );
                          if (doctor) {
                            setRecipient(doctor.id);
                            const grant = result.grants.find(
                              (g) =>
                                g.recipient_id === doctor.id && !g.revoked_at,
                            );
                            setPermissions(grant?.permissions ?? {});
                          }
                          setNotice(
                            "Doctor connected. Select tabs below and press Save access to finish.",
                          );
                        } catch (e) {
                          setError((e as Error).message);
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Connect doctor
                    </button>
                  </>
                )}
                <label>
                  Share with
                  <select
                    aria-label="Share with"
                    required
                    value={recipient}
                    onChange={(e) => select(e.target.value)}
                  >
                    <option value="">
                      Choose{" "}
                      {role === "DOCTOR" ? "connected doctor" : "family member"}
                    </option>
                    {recipients.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {!recipients.length && data && (
                <p className="hs-muted">
                  {role === "DOCTOR"
                    ? "Connect an approved doctor using their referral ID."
                    : "An accepted family invitation is required before sharing."}
                </p>
              )}
            </section>
            <section className="hs-section">
              <div className="hs-section-heading">
                <h2>
                  <b>2</b>Select what to share
                </h2>
                <button
                  className="hs-primary"
                  type="submit"
                  disabled={
                    !recipient || !Object.keys(permissions).length || busy
                  }
                >
                  {busy ? "Saving..." : "Save access"}
                </button>
                <div>
                  <button
                    type="button"
                    onClick={() =>
                      setPermissions(
                        Object.fromEntries(tabs.map(([id]) => [id, "view"])),
                      )
                    }
                  >
                    Select all · View
                  </button>
                  <button type="button" onClick={() => setPermissions({})}>
                    Clear selection
                  </button>
                </div>
              </div>
              <div className="hs-tabs">
                {tabs.map(([id, label], i) => {
                  const I = icons[i % icons.length];
                  return (
                    <div
                      className={
                        "hs-tab " + (permissions[id] ? "selected" : "")
                      }
                      key={id}
                    >
                      <label>
                        <input
                          type="checkbox"
                          checked={Boolean(permissions[id])}
                          onChange={(e) =>
                            setPermissions((old) => {
                              const next = { ...old };
                              if (e.target.checked) next[id] = "view";
                              else delete next[id];
                              return next;
                            })
                          }
                        />
                        <I />
                        <strong>{label}</strong>
                      </label>
                      <select
                        aria-label={label + " permission"}
                        disabled={!permissions[id]}
                        value={permissions[id] ?? "view"}
                        onChange={(e) =>
                          setPermissions((old) => ({
                            ...old,
                            [id]: e.target.value as "view" | "edit",
                          }))
                        }
                      >
                        <option value="view">View only</option>
                        <option value="edit">View + Edit</option>
                      </select>
                    </div>
                  );
                })}
              </div>
            </section>
            <section className="hs-section">
              <h2>
                <b>3</b>Set access duration
              </h2>
              <div className="hs-duration">
                <label>
                  Access duration
                  <select
                    aria-label="Access duration"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                  >
                    <option value="unlimited">All time — until revoked</option>
                    <option value="7">7 days</option>
                    <option value="30">30 days</option>
                    <option value="90">90 days</option>
                    <option value="custom">Custom dates</option>
                  </select>
                </label>
                {duration === "custom" && (
                  <>
                    <label>
                      From
                      <input
                        aria-label="Start date & time"
                        type="datetime-local"
                        value={start}
                        onChange={(e) => setStart(e.target.value)}
                      />
                    </label>
                    <label>
                      To
                      <input
                        aria-label="Expiry date & time"
                        required
                        type="datetime-local"
                        value={end}
                        min={start || local(new Date().toISOString())}
                        onChange={(e) => setEnd(e.target.value)}
                      />
                    </label>
                  </>
                )}
              </div>
              <div className="hs-summary">
                <div>
                  <LockKeyhole />
                  <h3>Your control. Always.</h3>
                  <p>
                    You choose the tabs, access level and duration. All time
                    remains active until you revoke it.
                  </p>
                </div>
                <div>
                  <h3>Access summary</h3>
                  <p>
                    Sharing with:{" "}
                    <strong>
                      {data?.recipients.find((r) => r.id === recipient)?.name ||
                        "Choose a recipient"}
                    </strong>
                  </p>
                  <p>
                    Tabs:{" "}
                    {Object.keys(permissions)
                      .map((id) => data?.tabs[id])
                      .join(", ") || "Select what to share"}
                  </p>
                  <p>
                    Duration:{" "}
                    {duration === "unlimited"
                      ? "All time — until revoked"
                      : duration === "custom"
                        ? `${start || "Now"} → ${end || "Choose end"}`
                        : duration + " days"}
                  </p>
                  <button
                    className="hs-primary"
                    type="submit"
                    disabled={
                      !recipient || !Object.keys(permissions).length || busy
                    }
                  >
                    <Share2 size={16} />
                    {busy ? "Saving..." : "Share Access"}
                  </button>
                </div>
              </div>
            </section>
          </fieldset>
        </form>
      ) : panel === "manage" ? (
        <section className="hs-section">
          <h2>Manage shared access</h2>
          {data?.grants.length ? (
            data.grants.map((grant) => (
              <article className="hs-grant" key={grant.id}>
                <div>
                  <strong>{grant.name}</strong>
                  <small>
                    {grant.role === "DOCTOR" ? "Doctor" : "Family member"} ·{" "}
                    {grant.active
                      ? "Active"
                      : grant.revoked_at
                        ? "Revoked"
                        : "Scheduled or expired"}{" "}
                    ·{" "}
                    {grant.expires_at
                      ? new Date(grant.expires_at).toLocaleString()
                      : "All time"}
                  </small>
                  <p>
                    {Object.entries(grant.permissions)
                      .map(
                        ([id, mode]) =>
                          `${data.tabs[id] ?? id} (${mode === "edit" ? "View + Edit" : "View"})`,
                      )
                      .join(" · ")}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setRole(grant.role);
                    select(grant.recipient_id);
                    setPanel("share");
                  }}
                >
                  Change
                </button>
                {!grant.revoked_at && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await careApi(
                          path + "/" + grant.id,
                          undefined,
                          true,
                          "DELETE",
                        );
                        await load();
                        setNotice("Access revoked immediately.");
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    <X size={15} />
                    Revoke
                  </button>
                )}
              </article>
            ))
          ) : (
            <p className="hs-muted">No access shared yet.</p>
          )}
        </section>
      ) : (
        <section className="hs-section">
          <h2>Access history</h2>
          {events.length ? (
            events.map((row) => (
              <article className="hs-grant" key={row.id}>
                <History size={18} />
                <div>
                  <strong>
                    {row.name} · {row.action}
                  </strong>
                  <small>{new Date(row.created_at).toLocaleString()}</small>
                  <p>
                    {Object.keys(row.permissions)
                      .map((id) => data?.tabs[id] ?? id)
                      .join(", ")}
                  </p>
                </div>
              </article>
            ))
          ) : (
            <p className="hs-muted">
              New permission changes and revocations will appear here.
            </p>
          )}
        </section>
      )}
    </section>
  );
}
