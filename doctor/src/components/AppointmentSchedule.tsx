import { useEffect, useState, type FormEvent } from "react";
import { careApi } from "../../../app/src/lib/careApi";
import "../../../app/src/components/appointment-windows.css";
type Window = {
  id: string;
  start: string;
  end: string;
  capacity: number;
  days: number[];
};
type Schedule = { windows: Window[]; version: number };
const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const initial = (): Window[] => [
  {
    id: crypto.randomUUID(),
    start: "10:00",
    end: "12:00",
    capacity: 20,
    days: [0, 1, 2, 3, 4, 5, 6],
  },
  {
    id: crypto.randomUUID(),
    start: "13:00",
    end: "16:00",
    capacity: 20,
    days: [0, 1, 2, 3, 4, 5, 6],
  },
];
export default function AppointmentSchedule({
  onSaved,
}: {
  onSaved?: () => void;
}) {
  const [windows, setWindows] = useState<Window[]>([]),
    [version, setVersion] = useState(0),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    careApi<Schedule>("/doctors/appointment-schedule")
      .then((r) => {
        if (active) {
          setWindows(r.version ? r.windows : initial());
          setVersion(r.version);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  function update(id: string, change: Partial<Window>) {
    setWindows((old) =>
      old.map((w) => (w.id === id ? { ...w, ...change } : w)),
    );
    setNotice("");
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await careApi<Schedule>(
        "/doctors/appointment-schedule",
        { windows, version },
        true,
        "PUT",
      );
      setWindows(r.windows);
      setVersion(r.version);
      onSaved?.();
      setNotice(
        "Appointment schedule saved. Connected patients can now book available windows.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="ap-panel">
      <h2>Appointments · Set your availability</h2>
      <p>
        Set the number of patients you can see in each time window. Capacity
        resets for each date. All times are IST (Asia/Kolkata).
      </p>
      {loading ? (
        <p role="status">Loading appointment schedule…</p>
      ) : (
        <form onSubmit={save}>
          <fieldset
            disabled={busy}
            style={{ border: 0, padding: 0, margin: 0 }}
          >
            {windows.map((w, index) => (
              <div className="ap-window" key={w.id}>
                <h3>Time window {index + 1}</h3>
                <div className="ap-window-fields">
                  <label>
                    Start time
                    <input
                      aria-label={"Start time " + (index + 1)}
                      type="time"
                      required
                      value={w.start}
                      onChange={(e) => update(w.id, { start: e.target.value })}
                    />
                  </label>
                  <label>
                    End time
                    <input
                      aria-label={"End time " + (index + 1)}
                      type="time"
                      required
                      value={w.end}
                      onChange={(e) => update(w.id, { end: e.target.value })}
                    />
                  </label>
                  <label>
                    Patient capacity
                    <input
                      aria-label={"Patient capacity " + (index + 1)}
                      type="number"
                      min={1}
                      required
                      value={w.capacity || ""}
                      onChange={(e) =>
                        update(w.id, { capacity: Number(e.target.value) })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      setWindows((old) => old.filter((v) => v.id !== w.id))
                    }
                  >
                    Remove window {index + 1}
                  </button>
                </div>
                <div
                  className="ap-days"
                  role="group"
                  aria-label={"Working days " + (index + 1)}
                >
                  {days.map((day, i) => (
                    <label key={day}>
                      <input
                        type="checkbox"
                        checked={w.days.includes(i)}
                        onChange={(e) =>
                          update(w.id, {
                            days: e.target.checked
                              ? [...w.days, i].sort()
                              : w.days.filter((d) => d !== i),
                          })
                        }
                      />
                      {day}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            {!windows.length && <p>No appointment windows configured.</p>}
            <div className="ap-actions">
              <button
                type="button"
                onClick={() =>
                  setWindows((old) => [
                    ...old,
                    {
                      id: crypto.randomUUID(),
                      start: "16:00",
                      end: "18:00",
                      capacity: 10,
                      days: [0, 1, 2, 3, 4, 5],
                    },
                  ])
                }
              >
                Add time window
              </button>
              <button type="submit">
                {busy ? "Saving…" : "Save appointment schedule"}
              </button>
            </div>
          </fieldset>
        </form>
      )}
      {error && (
        <div role="alert" className="ap-error">
          <p>{error}</p>
          <button disabled={busy} onClick={() => setAttempt((n) => n + 1)}>
            Reload saved schedule
          </button>
        </div>
      )}
      {notice && (
        <p role="status" className="ap-notice">
          {notice}
        </p>
      )}
    </section>
  );
}
