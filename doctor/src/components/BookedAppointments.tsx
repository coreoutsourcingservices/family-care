import { useEffect, useState } from "react";
import { ApiError } from "../../../app/src/lib/authApi";
import { downloadReport } from "../../../app/src/lib/healthProfiles";
import { careApi } from "../../../app/src/lib/careApi";
type Appointment = {
  id: string;
  profile_id: string;
  patient_name: string;
  start: string;
  end: string;
  status: string;
  email_status?: string;
  details?: { mode?: string; fee_paise?: number; notes?: string };
  documents?: { id: string; name: string }[];
};
const appointmentToday = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(
    new Date(),
  );
const appointmentClock = (value: string) => value;
type Window = {
  id: string;
  start: string;
  end: string;
  capacity: number;
  days: number[];
};
export default function BookedAppointments({
  refreshKey = 0,
}: {
  refreshKey?: number;
}) {
  const [windows, setWindows] = useState<Window[]>([]);
  const [date, setDate] = useState(appointmentToday),
    [items, setItems] = useState<Appointment[]>([]),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setItems([]);
    setError("");
    const load = () =>
      Promise.all([
        careApi<{ items: Appointment[] }>(
          "/doctors/booked-appointments?date=" + date,
        ),
        careApi<{ windows: Window[] }>("/doctors/appointment-schedule"),
      ])
        .then(([r, schedule]) => {
          if (active) {
            setItems(r.items);
            setWindows(schedule.windows);
            setError("");
          }
        })
        .catch((e) => {
          if (active)
            setError(
              e instanceof ApiError && e.status === 404
                ? "Appointment service needs the updated backend. Restart the local API to activate bookings."
                : e.message,
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    void load();
    const timer = setInterval(() => void load(), 30000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [date, attempt, refreshKey]);
  async function update(row: Appointment, status: string) {
    if (
      status === "CANCELLED" &&
      !confirm("Cancel this patient’s appointment?")
    )
      return;
    setBusy(true);
    setError("");
    try {
      await careApi(
        "/doctors/booked-appointments/" + row.id + "/status",
        { status },
        true,
        "PATCH",
      );
      setAttempt((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="ap-panel">
      <h2>Booked appointments</h2>
      <p>
        Connected patients with a reserved place in your time windows. Times are
        IST.
      </p>
      <label>
        Booking date
        <input
          type="date"
          value={date}
          disabled={busy}
          onChange={(e) => {
            if (e.target.value) setDate(e.target.value);
          }}
        />
      </label>
      {error && (
        <p role="alert" className="ap-error">
          {error}
        </p>
      )}

      {!loading && !error && (
        <div className="dr-slot-capacities">
          {windows
            .filter((w) =>
              w.days.includes(
                (new Date(date + "T12:00:00Z").getUTCDay() + 6) % 7,
              ),
            )
            .map((w) => {
              const booked = items.filter(
                (r) =>
                  r.start === w.start &&
                  r.end === w.end &&
                  ["BOOKED", "COMPLETED"].includes(r.status),
              ).length;
              const remaining = Math.max(0, w.capacity - booked);
              return (
                <article data-full={remaining === 0} key={w.id}>
                  <strong>
                    {w.start} - {w.end}
                  </strong>
                  <span>
                    {booked} / {w.capacity} booked
                  </span>
                  <small>
                    {remaining === 0 ? "FULL" : remaining + " places available"}
                  </small>
                </article>
              );
            })}
        </div>
      )}
      {error ? null : loading ? (
        <p role="status">Loading bookings…</p>
      ) : !items.length ? (
        <p>No bookings for this date.</p>
      ) : (
        <div className="ap-table-wrap">
          <table className="ap-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Window</th>
                <th>Status</th>
                <th>Email</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.patient_name}</strong>
                    <p>
                      {row.details?.mode === "video"
                        ? "Video"
                        : row.details?.mode === "physical"
                          ? "In-person"
                          : "Consultation"}
                      {row.details?.fee_paise != null
                        ? ` - INR ${row.details.fee_paise / 100}`
                        : ""}
                    </p>
                    {row.details?.notes || row.documents?.length ? (
                      <details>
                        <summary>Notes & documents</summary>
                        {row.details?.notes && (
                          <p style={{ whiteSpace: "pre-wrap" }}>
                            {row.details.notes}
                          </p>
                        )}
                        {row.documents?.map((document) => (
                          <button
                            key={document.id}
                            onClick={async () => {
                              try {
                                await downloadReport({
                                  id: document.id,
                                  name: document.name,
                                  addedAt: "",
                                  downloadPath: `/api/v1/doctors/booked-appointments/${row.id}/documents/${document.id}`,
                                });
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            {document.name}
                          </button>
                        ))}
                      </details>
                    ) : null}
                  </td>
                  <td>
                    {appointmentClock(row.start)} – {appointmentClock(row.end)}
                  </td>
                  <td>{row.status}</td>
                  <td>
                    {row.email_status === "SENT"
                      ? "Sent"
                      : row.email_status === "PENDING"
                        ? "Queued"
                        : (row.email_status ?? "—")}
                  </td>
                  <td>
                    {row.status === "BOOKED" && (
                      <div className="ap-actions">
                        <button
                          disabled={busy}
                          onClick={() => void update(row, "COMPLETED")}
                        >
                          Mark completed
                        </button>
                        <button
                          disabled={busy}
                          onClick={() => void update(row, "CANCELLED")}
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
