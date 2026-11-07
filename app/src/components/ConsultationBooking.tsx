import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowLeft,
  CalendarDays,
  MapPin,
  Video,
  Stethoscope,
  Upload,
  X,
} from "lucide-react";
import { careApi } from "../lib/careApi";
import "./consultation-booking.css";
export type BookingDoctor = {
  id: string;
  name: string;
  referral_id?: string;
  specialization?: string;
  qualification?: string;
  experience?: number;
  photo?: { url: string } | null;
};
type Options = {
  physical_enabled: boolean;
  video_enabled: boolean;
  physical_fee_paise: number | null;
  video_fee_paise: number | null;
};
type Window = {
  id: string;
  start: string;
  end: string;
  status: string;
  remaining: number;
};
export type Booking = {
  id: string;
  doctor_name: string;
  appointment_date: string;
  start: string;
  end: string;
  status: string;
  details?: { mode?: string; fee_paise?: number; notes?: string };
};
const today = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(
    new Date(),
  );
export default function ConsultationBooking({
  profileId,
  doctor,
  onBack,
  onBooked,
}: {
  profileId: string;
  doctor: BookingDoctor;
  onBack: () => void;
  onBooked: () => void;
}) {
  const [date, setDate] = useState(today),
    [month, setMonth] = useState(() => today().slice(0, 7)),
    [items, setItems] = useState<Window[]>([]),
    [options, setOptions] = useState<Options>(),
    [clinicAddress, setClinicAddress] = useState(""),
    [mode, setMode] = useState<"physical" | "video">("physical"),
    [slot, setSlot] = useState(""),
    [notes, setNotes] = useState(""),
    [files, setFiles] = useState<File[]>([]),
    [uploaded, setUploaded] = useState<Record<string, string>>({}),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [attempt, setAttempt] = useState(0);
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());
  useEffect(() => {
    let active = true;
    setItems([]);
    setOptions(undefined);
    setSlot("");
    setError("");
    setLoading(true);
    careApi<{
      items: Window[];
      doctor: {
        consultation_options?: Options;
        clinic_address?: string;
      } | null;
    }>(
      `/patients/profiles/${profileId}/appointment-availability?date=${date}&doctor_id=${doctor.id}`,
    )
      .then((data) => {
        if (active) {
          const settings = data.doctor?.consultation_options;
          const normalized: Options = {
            physical_enabled: settings?.physical_enabled ?? true,
            video_enabled: settings?.video_enabled ?? false,
            physical_fee_paise: settings?.physical_fee_paise ?? null,
            video_fee_paise: settings?.video_fee_paise ?? null,
          };
          setItems(Array.isArray(data.items) ? data.items : []);
          setClinicAddress(data.doctor?.clinic_address ?? "");
          setOptions(normalized);
          setMode((old) =>
            normalized[`${old}_enabled`]
              ? old
              : normalized.physical_enabled
                ? "physical"
                : "video",
          );
          if (!data.doctor)
            setError(
              "Connect this doctor to the profile or restart the updated appointment service, then retry.",
            );
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
  }, [profileId, doctor.id, date, attempt]);
  const fee = options?.[`${mode}_fee_paise`];
  const lastDay = new Date(today() + "T12:00:00Z");
  lastDay.setUTCDate(lastDay.getUTCDate() + 90);
  const maxDate = lastDay.toISOString().slice(0, 10);
  const monthDate = new Date(month + "-01T12:00:00");
  const days = new Date(
    monthDate.getFullYear(),
    monthDate.getMonth() + 1,
    0,
  ).getDate();
  const offset = (monthDate.getDay() + 6) % 7;
  function moveMonth(delta: number) {
    const d = new Date(
      monthDate.getFullYear(),
      monthDate.getMonth() + delta,
      1,
      12,
    );
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy || !slot || fee == null) return;
    setBusy(true);
    setError("");
    try {
      const ids: string[] = [];
      const next = { ...uploaded };
      for (const file of files) {
        const key = [file.name, file.size, file.lastModified].join(":");
        if (!next[key]) {
          const form = new FormData();
          form.append("file", file);
          const result = await careApi<{ report: { id: string } }>(
            `/patients/profiles/${profileId}/reports`,
            form,
          );
          next[key] = result.report.id;
          setUploaded({ ...next });
        }
        ids.push(next[key]);
      }
      const result = await careApi<{ appointment: Booking }>(
        `/patients/profiles/${profileId}/appointments`,
        {
          doctor_id: doctor.id,
          window_id: slot,
          appointment_date: date,
          request_id: requestId,
          mode,
          expected_fee_paise: fee,
          notes,
          report_ids: ids,
        },
      );
      setNotice(
        `Booked with ${result.appointment.doctor_name} on ${date}, ${result.appointment.start}-${result.appointment.end} IST.`,
      );
      onBooked();
    } catch (e) {
      setError((e as Error).message);
      setRequestId(crypto.randomUUID());
      setAttempt((n) => n + 1);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="cb-page">
      <button className="cb-back" onClick={onBack} disabled={busy}>
        <ArrowLeft size={17} />
        Back to doctors
      </button>
      <div className="cb-heading">
        <span>YOUR CONSULTATION</span>
        <h1>Book a consultation</h1>
        <p>Choose your visit mode, date and an available time window.</p>
      </div>
      {notice ? (
        <section className="cb-card" role="status">
          <h2>Appointment booked</h2>
          <p>{notice}</p>
          <button className="cb-primary" onClick={onBack}>
            View consultations
          </button>
        </section>
      ) : (
        <form className="cb-grid" onSubmit={submit}>
          <aside className="cb-card cb-doctor">
            <div className="cb-avatar">
              {doctor.photo?.url ? (
                <img src={doctor.photo.url} alt="" />
              ) : (
                <Stethoscope />
              )}
            </div>
            <h2>{doctor.name}</h2>
            <p>
              {doctor.specialization ||
                doctor.qualification ||
                "Registered doctor"}
            </p>
            {doctor.experience != null && (
              <p>{doctor.experience} years experience</p>
            )}
            <small>Referral ID: {doctor.referral_id || "Not available"}</small>
            <h3>Consultation mode</h3>
            {mode === "physical" && clinicAddress && (
              <p>
                <MapPin size={15} /> {clinicAddress}
              </p>
            )}
            {(["physical", "video"] as const)
              .filter((value) => options?.[`${value}_enabled`])
              .map((value) => (
                <button
                  disabled={busy}
                  key={value}
                  type="button"
                  className={"cb-mode " + (mode === value ? "selected" : "")}
                  onClick={() => setMode(value)}
                >
                  {value === "physical" ? <MapPin /> : <Video />}
                  <span>
                    <strong>
                      {value === "physical"
                        ? "In-person visit"
                        : "Video consultation"}
                    </strong>
                    <small>
                      {options?.[`${value}_fee_paise`] == null
                        ? "Fee not set"
                        : new Intl.NumberFormat("en-IN", {
                            style: "currency",
                            currency: "INR",
                          }).format(options[`${value}_fee_paise`]! / 100)}
                    </small>
                  </span>
                </button>
              ))}
            {options && fee == null && (
              <p role="status">
                The doctor needs to set a fee before this mode can be booked.
              </p>
            )}
            <p className="cb-muted">
              Fees shown are for the consultation. No payment is collected here.
              Video arrangements are provided by the doctor.
            </p>
          </aside>
          <div className="cb-card">
            <h2>
              <CalendarDays size={21} />
              Choose a date & time
            </h2>
            <div className="cb-calendar">
              <nav>
                <button
                  type="button"
                  aria-label="Previous month"
                  onClick={() => moveMonth(-1)}
                >
                  &lt;
                </button>
                <strong>
                  {monthDate.toLocaleDateString("en-IN", {
                    month: "long",
                    year: "numeric",
                  })}
                </strong>
                <button
                  type="button"
                  aria-label="Next month"
                  onClick={() => moveMonth(1)}
                >
                  &gt;
                </button>
              </nav>
              <div className="cb-days">
                {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                  (day) => (
                    <small key={day}>{day}</small>
                  ),
                )}
                {Array.from({ length: offset }, (_, i) => (
                  <span key={"blank" + i} />
                ))}
                {Array.from({ length: days }, (_, i) => {
                  const value = month + "-" + String(i + 1).padStart(2, "0");
                  return (
                    <button
                      type="button"
                      key={value}
                      disabled={value < today() || value > maxDate || busy}
                      className={date === value ? "selected" : ""}
                      onClick={() => {
                        setDate(value);
                        setRequestId(crypto.randomUUID());
                      }}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>
            </div>
            <h3>
              Available times - {date} <small>IST</small>
            </h3>
            {loading ? (
              <p role="status">Checking available times...</p>
            ) : items.length ? (
              <div className="cb-slots">
                {items.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    disabled={busy || item.status !== "AVAILABLE"}
                    className={slot === item.id ? "selected" : ""}
                    onClick={() => {
                      setSlot(item.id);
                      setRequestId(crypto.randomUUID());
                    }}
                  >
                    <strong>
                      {item.start} - {item.end}
                    </strong>
                    <small>
                      {item.status === "AVAILABLE"
                        ? `${item.remaining} places available`
                        : item.status}
                    </small>
                  </button>
                ))}
              </div>
            ) : (
              <p>No appointment windows on this date. Choose another date.</p>
            )}
            <label>
              Notes for the doctor
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                maxLength={2000}
                rows={3}
                placeholder="Symptoms, questions or anything you want the doctor to know"
                disabled={busy}
              />
            </label>
            <label className="cb-upload">
              <Upload size={18} />
              Optional documents
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.webp"
                disabled={busy}
                onChange={(e) => {
                  const chosen = Array.from(e.target.files ?? []);
                  if (chosen.length > 10) {
                    setError("Choose up to 10 documents.");
                    return;
                  }
                  setFiles(chosen);
                }}
              />
            </label>
            {files.map((file, i) => (
              <div className="cb-file" key={i}>
                <span>{file.name}</span>
                <button
                  type="button"
                  disabled={busy}
                  aria-label={"Remove " + file.name}
                  onClick={() => setFiles(files.filter((_, n) => n !== i))}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
            <small className="cb-muted">
              Attached documents are saved to this profile reports and shared
              with the booked doctor for this consultation.
            </small>
            {error && (
              <p role="alert" className="cb-error">
                {error}
                <button type="button" onClick={() => setAttempt((n) => n + 1)}>
                  Retry availability
                </button>
              </p>
            )}
            <button
              className="cb-primary"
              disabled={busy || loading || !slot || fee == null}
            >
              {busy
                ? "Saving booking..."
                : `Book ${mode === "physical" ? "in-person" : "video"} consultation`}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
export function ConsultationBookings({
  profileId,
  revision = 0,
}: {
  profileId: string;
  revision?: number;
}) {
  const [items, setItems] = useState<Booking[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    careApi<{ items: Booking[] }>(
      `/patients/profiles/${profileId}/appointments`,
    )
      .then((data) => {
        if (active) setItems(data.items);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [profileId, revision]);
  return (
    <section className="cb-card cb-history">
      <h2>Booked consultations</h2>
      {error && <p role="alert">{error}</p>}
      {items.length ? (
        items.map((item) => (
          <article key={item.id}>
            <div>
              <strong>{item.doctor_name}</strong>
              <p>
                {item.appointment_date} - {item.start} - {item.end} IST
              </p>
              <small>
                {item.details?.mode === "video"
                  ? "Video"
                  : item.details?.mode === "physical"
                    ? "In-person"
                    : "Consultation"}{" "}
                - {item.status}
                {item.details?.fee_paise != null
                  ? ` - INR ${item.details.fee_paise / 100}`
                  : ""}
              </small>
            </div>
            {item.status === "BOOKED" && (
              <button
                onClick={async () => {
                  try {
                    const data = await careApi<{ appointment: Booking }>(
                      `/patients/profiles/${profileId}/appointments/${item.id}/status`,
                      { status: "CANCELLED" },
                      true,
                      "PATCH",
                    );
                    setItems((old) =>
                      old.map((row) =>
                        row.id === item.id ? data.appointment : row,
                      ),
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Cancel booking
              </button>
            )}
          </article>
        ))
      ) : (
        <p>No booked consultations yet.</p>
      )}
    </section>
  );
}
