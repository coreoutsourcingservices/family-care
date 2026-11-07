import { useEffect, useState, type FormEvent } from "react";
import { Plus, Search, Stethoscope, UserRound, X } from "lucide-react";
import CareProfileHeader from "../../../../app/src/components/CareProfileHeader";
import ProfileDoctorConnection from "../../../../app/src/components/ProfileDoctorConnection";
import { careApi } from "../../../../app/src/lib/careApi";
import { type SectionProps } from "./childRecords";
import type { HealthProfile } from "../../../../app/src/lib/healthProfiles";
import "./child-doctor-directory.css";
import ConsultationBooking, {
  ConsultationBookings,
} from "../../../../app/src/components/ConsultationBooking";
type Doctor = {
  id: string;
  name: string;
  specialization: string;
  qualification: string;
  referral_id: string;
  public_id?: string;
  experience: number;
  photo?: { url: string } | null;
};
export default function DoctorConsultation({
  profile,
  onRefresh,
  entries,
}: SectionProps & { profile: HealthProfile; onRefresh: () => Promise<void> }) {
  const [selected, setSelected] = useState<Doctor>(),
    [bookingRevision, setBookingRevision] = useState(0);
  const [open, setOpen] = useState(false),
    [code, setCode] = useState(""),
    [search, setSearch] = useState(""),
    [doctors, setDoctors] = useState<Doctor[]>([]),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    const timer = setTimeout(() => {
      careApi<{ items: Doctor[]; total: number }>(
        `/patients/doctor-directory?search=${encodeURIComponent(search.trim())}&page=${page}&per_page=12`,
      )
        .then((result) => {
          if (active) {
            setDoctors(result.items);
            setTotal(result.total);
          }
        })
        .catch((e) => {
          if (active) {
            setDoctors([]);
            setTotal(0);
            setError(e.message);
          }
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [search, page]);
  async function connect(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await careApi("/patients/profiles/" + profile.id + "/connect-doctor", {
        referral_id: code.trim(),
      });
      await onRefresh();
      setCode("");
      setOpen(false);
      setNotice("Doctor connected successfully.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not connect doctor.");
    } finally {
      setBusy(false);
    }
  }
  if (selected)
    return (
      <ConsultationBooking
        key={profile.id + selected.id}
        profileId={profile.id}
        doctor={selected}
        onBack={() => setSelected(undefined)}
        onBooked={() => setBookingRevision((n) => n + 1)}
      />
    );
  return (
    <>
      <CareProfileHeader
        name={profile.name}
        dob={profile.dob}
        entries={entries}
      />
      <div className="ch-page-heading">
        <div>
          <h1>Doctor consultation</h1>
          <p>Find an approved doctor and connect using their referral ID.</p>
        </div>
        <button
          className="ch-button"
          aria-expanded={open}
          aria-controls="child-add-doctor"
          onClick={() => {
            setOpen(!open);
            setError("");
          }}
        >
          {open ? <X size={16} /> : <Plus size={16} />}Add doctor
        </button>
      </div>
      {open && (
        <section className="ch-panel ch-doctor-connect" id="child-add-doctor">
          <form onSubmit={connect}>
            <label htmlFor="child-doctor-referral">
              Doctor referral ID
              <input
                autoFocus
                id="child-doctor-referral"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Enter doctor referral ID"
                required
                maxLength={160}
              />
            </label>
            <button
              type="submit"
              className="ch-button"
              disabled={busy || !code.trim()}
            >
              {busy ? "Connecting..." : "Connect doctor"}
            </button>
          </form>
          <p>
            Connecting a doctor gives them the access described in your profile
            sharing settings.
          </p>
        </section>
      )}
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {profile.referral.doctor && (
        <ProfileDoctorConnection profile={profile} onRefresh={onRefresh} />
      )}
      <section
        className="ch-panel ch-doctor-directory"
        aria-label="Doctor directory"
      >
        <div className="ch-section-top">
          <h2>Find a doctor</h2>
          <small>{total} approved doctors</small>
        </div>
        <label className="ch-doctor-search">
          <Search size={18} />
          <input
            aria-label="Search child doctors"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
              setError("");
            }}
            placeholder="Search doctor name or specialty"
          />
        </label>
        {loading ? (
          <p role="status">Finding doctors...</p>
        ) : doctors.length ? (
          <div className="ch-directory-grid">
            {doctors.map((doctor) => (
              <article key={doctor.id}>
                <div className="ch-directory-person">
                  <span>
                    {doctor.photo?.url ? (
                      <img src={doctor.photo.url} alt="" />
                    ) : (
                      <UserRound size={24} />
                    )}
                  </span>
                  <div>
                    <h3>{doctor.name}</h3>
                    <p>
                      {doctor.specialization ||
                        doctor.qualification ||
                        "Registered doctor"}
                    </p>
                  </div>
                </div>
                <p className="ch-directory-id">
                  <strong>Referral ID</strong>
                  <span>{doctor.referral_id}</span>
                </p>
                {doctor.public_id && (
                  <small>Doctor ID: {doctor.public_id}</small>
                )}
                <button
                  className="ch-button"
                  disabled={
                    busy || profile.referral.code === doctor.referral_id
                  }
                  onClick={() => {
                    setCode(doctor.referral_id);
                    setOpen(true);
                    requestAnimationFrame(() =>
                      document
                        .getElementById("child-add-doctor")
                        ?.scrollIntoView({ block: "center" }),
                    );
                  }}
                >
                  <Stethoscope size={15} />
                  {profile.referral.code === doctor.referral_id
                    ? "Connected"
                    : "Use referral ID"}
                </button>
                <button
                  className="ch-button"
                  onClick={() => setSelected(doctor)}
                >
                  Request consultation
                </button>
              </article>
            ))}
          </div>
        ) : (
          <p>No approved doctors match your search.</p>
        )}
        <div className="ch-directory-pagination">
          <button
            disabled={page === 1 || loading}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <span>Page {page}</span>
          <button
            disabled={page * 12 >= total || loading}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      </section>
      <ConsultationBookings profileId={profile.id} revision={bookingRevision} />
    </>
  );
}
