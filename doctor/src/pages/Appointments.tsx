import AppointmentSchedule from "../components/AppointmentSchedule";
import BookedAppointments from "../components/BookedAppointments";
import { X, CalendarClock, ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import WorkspacePage, {
  useWorkspaceData,
  PageStatus,
  PageSearch,
} from "../components/WorkspacePage";
import { careApi } from "../lib/workspaceApi";
type Visit = {
  id: string;
  patient_name: string;
  concern: string;
  status: string;
  requested_at: string;
  confirmed_at: string | null;
  duration_minutes: number;
  version: number;
};
const localTime = (value: string) => {
  const d = new Date(value);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}T${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};
export default function Appointments() {
  const visits = useWorkspaceData("Appointments:1",
    async () =>
      (await careApi<{ items: Visit[] }>("/doctors/consultation-visits")).items,
  );
  const [showSlots, setShowSlots] = useState(false);
  const [slotsRevision, setSlotsRevision] = useState(0);
  const [selectedDate, setSelectedDate] = useState(""),
    [search, setSearch] = useState(""),
    [month, setMonth] = useState(
      () => new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    );
  const dateKey = (d: Date) =>
    [
      d.getFullYear(),
      String(d.getMonth() + 1).padStart(2, "0"),
      String(d.getDate()).padStart(2, "0"),
    ].join("-");
  const calendar = Array.from(
    {
      length: new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate(),
    },
    (_, i) => new Date(month.getFullYear(), month.getMonth(), i + 1),
  );
  const [status, setStatus] = useState("all"),
    [editing, setEditing] = useState<Visit>(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function update(
    row: Visit,
    value: string,
    confirmed_at?: string,
    duration_minutes = 30,
  ) {
    setBusy(true);
    setError("");
    try {
      await careApi(
        `/doctors/consultation-visits/${row.id}/status`,
        {
          status: value,
          version: row.version,
          ...(confirmed_at
            ? {
                confirmed_at: new Date(confirmed_at).toISOString(),
                duration_minutes,
              }
            : {}),
        },
        true,
        "PATCH",
      );
      setEditing(undefined);
      visits.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <WorkspacePage
      title="Appointments"
      description="Requested times stay unconfirmed until you confirm a time. All times below use your device timezone."
      refresh={() => {
        visits.refresh();
      }}
    >
      {error && (
        <p className="dw-error" role="alert">
          {error}
        </p>
      )}
      <div className="dr-appointments-toolbar">
        <h2>Patient appointments</h2>
        <button className="button primary" onClick={() => setShowSlots(true)}>
          <CalendarClock size={17} />
          Manage Slots
        </button>
      </div>
      {showSlots && (
        <div className="dr-slots-overlay" onClick={() => setShowSlots(false)}>
          <section
            className="dr-slots-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Manage custom appointment slots"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="dr-dialog-close"
              aria-label="Close slot settings"
              onClick={() => setShowSlots(false)}
            >
              <X />
            </button>
            <AppointmentSchedule
              onSaved={() => setSlotsRevision((n) => n + 1)}
            />
          </section>
        </div>
      )}
      <BookedAppointments refreshKey={slotsRevision} />

      {!!visits.data?.length && (
        <>
          <div className="dw-toolbar">
            <PageSearch
              value={search}
              onChange={setSearch}
              placeholder="Search appointments"
            />
            <label className="dw-filter-label">
              Appointment status
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="all">All</option>
                {[
                  "REQUESTED",
                  "CONFIRMED",
                  "DECLINED",
                  "CANCELLED",
                  "COMPLETED",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="dr-appointment-layout">
            <aside className="dw-panel dr-calendar">
              <div>
                <button
                  aria-label="Previous month"
                  onClick={() =>
                    setMonth(
                      new Date(month.getFullYear(), month.getMonth() - 1, 1),
                    )
                  }
                >
                  <ChevronLeft size={16} />
                </button>
                <strong>
                  {month.toLocaleDateString("en-IN", {
                    month: "long",
                    year: "numeric",
                  })}
                </strong>
                <button
                  aria-label="Next month"
                  onClick={() =>
                    setMonth(
                      new Date(month.getFullYear(), month.getMonth() + 1, 1),
                    )
                  }
                >
                  <ChevronRight size={16} />
                </button>
              </div>
              <div className="dr-calendar-days">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                  <small key={d}>{d}</small>
                ))}
                {Array.from({ length: month.getDay() }, (_, i) => (
                  <span key={"blank" + i} />
                ))}
                {calendar.map((d) => (
                  <button
                    className={selectedDate === dateKey(d) ? "active" : ""}
                    key={dateKey(d)}
                    onClick={() => setSelectedDate(dateKey(d))}
                  >
                    {d.getDate()}
                  </button>
                ))}
              </div>
              <button
                className="dw-secondary"
                onClick={() => setSelectedDate("")}
              >
                Show all dates
              </button>
            </aside>
            <div>
              {selectedDate && (
                <p className="dw-info">Appointments for {selectedDate}</p>
              )}
              {editing && (
                <form
                  className="dw-panel clinical-form-grid"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const data = new FormData(e.currentTarget);
                    void update(
                      editing,
                      "CONFIRMED",
                      String(data.get("time")),
                      Number(data.get("duration")),
                    );
                  }}
                >
                  <h3>
                    {editing.status === "CONFIRMED" ? "Reschedule" : "Confirm"}:{" "}
                    {editing.patient_name}
                  </h3>
                  <label>
                    Confirmed start
                    <input
                      type="datetime-local"
                      name="time"
                      defaultValue={localTime(
                        editing.confirmed_at || editing.requested_at,
                      )}
                      required
                    />
                  </label>
                  <label>
                    Duration (minutes)
                    <input
                      type="number"
                      min={5}
                      max={240}
                      name="duration"
                      defaultValue={editing.duration_minutes || 30}
                      required
                    />
                  </label>
                  <button disabled={busy} className="button primary">
                    Confirm appointment
                  </button>
                  <button type="button" onClick={() => setEditing(undefined)}>
                    Cancel changes
                  </button>
                </form>
              )}
              <PageStatus
                loading={visits.loading}
                error={visits.error}
                empty={!visits.data?.length}
                emptyTitle="No consultation requests"
              >
                <div className="dw-panel dw-table-wrap">
                  <table className="dw-table">
                    <thead>
                      <tr>
                        <th>Patient</th>
                        <th>Concern</th>
                        <th>Requested time</th>
                        <th>Confirmed time</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visits.data
                        ?.filter(
                          (row) =>
                            (status === "all" || row.status === status) &&
                            (!selectedDate ||
                              dateKey(
                                new Date(row.confirmed_at || row.requested_at),
                              ) === selectedDate) &&
                            `${row.patient_name} ${row.concern}`
                              .toLowerCase()
                              .includes(search.toLowerCase()),
                        )
                        .map((row) => (
                          <tr key={row.id}>
                            <td>{row.patient_name}</td>
                            <td>{row.concern}</td>
                            <td>
                              {new Date(row.requested_at).toLocaleString(
                                "en-IN",
                              )}
                            </td>
                            <td>
                              {row.confirmed_at
                                ? new Date(row.confirmed_at).toLocaleString(
                                    "en-IN",
                                  ) +
                                  " / " +
                                  row.duration_minutes +
                                  " min"
                                : "Not confirmed"}
                            </td>
                            <td>{row.status}</td>
                            <td>
                              <div className="dw-row-actions">
                                {["REQUESTED", "CONFIRMED"].includes(
                                  row.status,
                                ) && (
                                  <>
                                    <button
                                      disabled={busy}
                                      onClick={() => setEditing(row)}
                                    >
                                      {row.status === "CONFIRMED"
                                        ? "Reschedule"
                                        : "Confirm time"}
                                    </button>
                                    <button
                                      disabled={busy}
                                      onClick={() => {
                                        if (
                                          confirm(
                                            "Cancel this appointment request?",
                                          )
                                        )
                                          void update(row, "CANCELLED");
                                      }}
                                    >
                                      Cancel
                                    </button>
                                  </>
                                )}
                                {row.status === "REQUESTED" && (
                                  <button
                                    disabled={busy}
                                    onClick={() => void update(row, "DECLINED")}
                                  >
                                    Decline
                                  </button>
                                )}
                                {row.status === "CONFIRMED" && (
                                  <button
                                    disabled={
                                      busy ||
                                      (!!row.confirmed_at &&
                                        Date.parse(row.confirmed_at) >
                                          Date.now())
                                    }
                                    onClick={() =>
                                      void update(row, "COMPLETED")
                                    }
                                  >
                                    Mark completed
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </PageStatus>
            </div>
          </div>
        </>
      )}
    </WorkspacePage>
  );
}
