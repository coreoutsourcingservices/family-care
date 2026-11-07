import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Stethoscope,
  Heart,
  CalendarDays,
  FileText,
  Share2,
  Star,
  Search,
  ArrowRight,
  UserRound,
  MessageCircle,
  Check,
  Clock3,
} from "lucide-react";
import { careApi } from "../lib/careApi";
import type { HealthProfile } from "../lib/healthProfiles";
import "./health-sharing.css";
import ConsultationBooking, {
  ConsultationBookings,
} from "./ConsultationBooking";
type Doctor = {
  id: string;
  name: string;
  specialization: string;
  qualification: string;
  experience: number;
  rating: number | null;
  review_count: number;
  referral_id: string;
  photo?: { url: string } | null;
};
type Visit = {
  id: string;
  doctor_id: string;
  doctor_name: string;
  concern: string;
  notes: string;
  requested_at: string;
  status: string;
  review_rating: number | null;
};
type SavedVisitNote = {
  id: string;
  date: string;
  title: string;
  doctor?: string;
  notes?: string;
  status?: string;
};
export default function DoctorConsultation({
  profile,
  history = [],
}: {
  profile: HealthProfile;
  history?: SavedVisitNote[];
}) {
  const women = profile.module === "women",
    base = "/patients/profiles/" + profile.id + "/consultations";
  const [doctors, setDoctors] = useState<Doctor[]>([]),
    [visits, setVisits] = useState<Visit[]>([]),
    [search, setSearch] = useState(""),
    [page, setPage] = useState(1),
    [total, setTotal] = useState(0),
    [concern, setConcern] = useState(
      women ? "Menstrual & cycle care" : "General health",
    ),
    [selected, setSelected] = useState<Doctor>(),
    [mode, setMode] = useState("consult"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [loading, setLoading] = useState(true);
  const concerns = women
    ? [
        "Menstrual & cycle care",
        "PCOS & hormonal",
        "Pregnancy care",
        "Fertility & conception",
        "Reproductive health",
        "Women's wellness",
        "Other concern",
      ]
    : [
        "General health",
        "Blood pressure",
        "Blood sugar",
        "Heart health",
        "Nutrition & lifestyle",
        "Preventive care",
        "Other concern",
      ];
  async function refresh() {
    setVisits((await careApi<{ items: Visit[] }>(base)).items);
  }
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const timer = setTimeout(() => {
      careApi<{ items: Doctor[]; total: number }>(
        `/patients/doctor-directory?search=${encodeURIComponent(search.trim())}&module=${profile.module}&concern=${encodeURIComponent(concern)}&page=${page}&per_page=6`,
      )
        .then((d) => {
          if (active) {
            setDoctors(d.items);
            setTotal(d.total);
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
    }, 250);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [search, page, concern, profile.module]);

  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [base]);
  const root = "/customer/" + profile.module;
  const future = visits
    .filter(
      (v) =>
        ["REQUESTED", "CONFIRMED"].includes(v.status) &&
        new Date(v.requested_at) > new Date(),
    )
    .sort((a, b) => a.requested_at.localeCompare(b.requested_at));
  const [bookingRevision, setBookingRevision] = useState(0);
  if (selected)
    return (
      <ConsultationBooking
        key={profile.id + selected.id}
        profileId={profile.id}
        doctor={selected}
        onBack={() => {
          setSelected(undefined);
          setMode("visits");
        }}
        onBooked={() => setBookingRevision((n) => n + 1)}
      />
    );
  return (
    <section className={"dc-page hs-" + profile.module}>
      <header className="hs-hero dc-hero">
        <span className="hs-hero-icon">
          <Stethoscope />
        </span>
        <div>
          <h1>
            {women ? "Women's Health" : "Adult Health"} — Doctor Consultation
          </h1>
          <p>
            Choose an approved doctor, request a time and keep your care
            connected.
          </p>
        </div>
      </header>
      <nav className="hs-nav">
        <button
          className={mode === "consult" ? "active" : ""}
          onClick={() => setMode("consult")}
        >
          <Stethoscope size={18} />
          Consult a doctor
        </button>
        <button
          className={mode === "visits" ? "active" : ""}
          onClick={() => setMode("visits")}
        >
          <CalendarDays size={18} />
          My consultations
        </button>
        <Link to={root + (women ? "/records" : "/medicine")}>
          <FileText size={18} />
          Prescriptions
        </Link>
        <Link to={root + (women ? "/records" : "/reports")}>
          <FileText size={18} />
          Reports & notes
        </Link>
      </nav>
      {error && (
        <p role="alert" className="hs-error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="hs-notice">
          <Check size={16} />
          {notice}
        </p>
      )}
      <div className="dc-columns">
        <div>
          {mode === "consult" ? (
            <>
              <section className="hs-section">
                <h2>Start a new consultation</h2>
                <div className="dc-steps">
                  <strong>1 · Select concern</strong>
                  <ArrowRight />
                  <span>2 · Choose doctor</span>
                  <ArrowRight />
                  <span>3 · Request time</span>
                </div>
                <h3>Select your concern</h3>
                <div className="dc-concerns">
                  {concerns.map((value, i) => {
                    const I = [
                      CalendarDays,
                      ActivityIcon,
                      Heart,
                      Stethoscope,
                      Heart,
                      UserRound,
                      MessageCircle,
                    ][i];
                    return (
                      <button
                        className={concern === value ? "selected" : ""}
                        key={value}
                        onClick={() => {
                          setConcern(value);
                          setPage(1);
                        }}
                      >
                        <I size={25} />
                        <strong>{value}</strong>
                      </button>
                    );
                  })}
                </div>
              </section>
              <section className="hs-section">
                <div className="hs-section-heading">
                  <h2>
                    {search.trim()
                      ? "Doctor search results"
                      : "Doctors for your concern"}
                  </h2>
                  <small>Highest patient ratings first</small>
                </div>
                <label className="dc-search">
                  <Search size={17} />
                  <input
                    aria-label="Search doctors"
                    placeholder="Search doctor name or specialty"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setPage(1);
                    }}
                  />
                </label>
                {loading ? (
                  <p role="status">Finding approved doctors...</p>
                ) : doctors.length ? (
                  <div className="dc-doctors">
                    {doctors.map((doctor) => (
                      <article key={doctor.id}>
                        <div className="dc-doctor-top">
                          <span className="dc-photo">
                            {doctor.photo?.url ? (
                              <img src={doctor.photo.url} alt="" />
                            ) : (
                              <UserRound />
                            )}
                          </span>
                          <div>
                            <h3>{doctor.name}</h3>
                            <p>
                              {doctor.specialization ||
                                doctor.qualification ||
                                "Registered doctor"}
                            </p>
                            <small>
                              {doctor.experience
                                ? doctor.experience + " years experience"
                                : "Experience not provided"}
                            </small>
                          </div>
                        </div>
                        <div className="dc-rating">
                          <Star size={17} />
                          {doctor.rating !== null ? (
                            <>
                              <strong>{doctor.rating.toFixed(1)}</strong>
                              <span>
                                ({doctor.review_count}{" "}
                                {doctor.review_count === 1
                                  ? "review"
                                  : "reviews"}
                                )
                              </span>
                            </>
                          ) : (
                            <span>Not rated yet</span>
                          )}
                        </div>
                        <span className="dc-approved">
                          <Check size={13} />
                          Approved doctor
                        </span>
                        <button
                          className="dc-consult"
                          onClick={() => setSelected(doctor)}
                        >
                          <Stethoscope size={16} />
                          Request consultation
                        </button>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="hs-muted">
                    No approved doctors match this concern or search. Try
                    another concern, or search for a doctor by name or
                    specialty.
                  </p>
                )}
                <div className="dc-paging">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    Previous
                  </button>
                  <small>
                    Page {page} · {total} doctors
                  </small>
                  <button
                    disabled={page * 6 >= total}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </button>
                </div>
              </section>
              <section className="hs-section dc-how">
                <h2>How it works</h2>
                <div>
                  {[
                    ["Choose concern", "Select your health need"],
                    ["Pick a doctor", "See real ratings and experience"],
                    ["Request a time", "Doctor confirms separately"],
                    ["Share if needed", "Choose tabs in Access & Sharing"],
                  ].map(([title, copy], i) => (
                    <div key={title}>
                      <b>{i + 1}</b>
                      <strong>{title}</strong>
                      <small>{copy}</small>
                    </div>
                  ))}
                </div>
              </section>
            </>
          ) : (
            <section className="hs-section">
              <h2>My consultations</h2>
              <ConsultationBookings
                profileId={profile.id}
                revision={bookingRevision}
              />
              {visits.length ? (
                visits.map((v) => (
                  <VisitCard
                    key={v.id}
                    visit={v}
                    refresh={refresh}
                    path={base}
                  />
                ))
              ) : (
                <p className="hs-muted">No consultation requests yet.</p>
              )}
              <SavedConsultationNotes records={history} />
            </section>
          )}
        </div>
        <aside>
          <section className="hs-section">
            <h2>
              <CalendarDays />
              Upcoming consultation
            </h2>
            {future.length ? (
              future
                .slice(0, 3)
                .map((v) => (
                  <VisitCard
                    key={v.id}
                    visit={v}
                    refresh={refresh}
                    path={base}
                  />
                ))
            ) : (
              <p className="hs-muted">
                Your requested and confirmed consultations will appear here.
              </p>
            )}
          </section>
          <section className="hs-section dc-quick">
            <h2>Quick actions</h2>
            <div>
              <Link to={root + (women ? "/records" : "/reports")}>
                <FileText />
                Upload reports
              </Link>
              <Link to={root + "/sharing"}>
                <Share2 />
                Share records
              </Link>
              <button
                onClick={() => {
                  setConcern("Other concern");
                  setMode("consult");
                }}
              >
                <MessageCircle />
                Ask a question
              </button>
              <Link to={root + (women ? "/records" : "/medicine")}>
                <FileText />
                View prescriptions
              </Link>
            </div>
          </section>
          <section className="hs-section">
            <h2>
              <Clock3 />
              Recent consultations
            </h2>
            {visits
              .filter((v) => v.status === "COMPLETED")
              .slice(0, 3)
              .map((v) => (
                <VisitCard key={v.id} visit={v} refresh={refresh} path={base} />
              ))}
            {!visits.some((v) => v.status === "COMPLETED") && (
              <p className="hs-muted">
                Completed consultations appear here. Ratings can be added after
                completion.
              </p>
            )}
            <SavedConsultationNotes
              records={history
                .slice()
                .sort((a, b) => b.date.localeCompare(a.date))
                .slice(0, 3)}
            />
          </section>
        </aside>
      </div>
    </section>
  );
}
function ActivityIcon(props: { size?: number }) {
  return <Heart {...props} />;
}
function VisitCard({
  visit,
  refresh,
  path,
}: {
  visit: Visit;
  refresh: () => Promise<void>;
  path: string;
}) {
  const [rating, setRating] = useState(String(visit.review_rating ?? 5)),
    [error, setError] = useState(""),
    [reviewing, setReviewing] = useState(false),
    [busy, setBusy] = useState(false);
  return (
    <article className="dc-visit">
      <strong>{visit.doctor_name}</strong>
      <small>{new Date(visit.requested_at).toLocaleString()}</small>
      <p>{visit.concern}</p>
      <span className={"dc-status " + visit.status.toLowerCase()}>
        {visit.status}
      </span>
      {["REQUESTED", "CONFIRMED"].includes(visit.status) && (
        <button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await careApi(path + "/" + visit.id + "/cancel", {});
              await refresh();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          Cancel request
        </button>
      )}
      {visit.status === "COMPLETED" && (
        <>
          <button onClick={() => setReviewing(!reviewing)}>
            {visit.review_rating
              ? "Edit rating · " + visit.review_rating + " ★"
              : "Rate consultation"}
          </button>
          {reviewing && (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const values = Object.fromEntries(
                  new FormData(e.currentTarget),
                );
                setBusy(true);
                try {
                  await careApi(
                    "/patients/doctor-directory/" + visit.doctor_id + "/review",
                    {
                      consultation_id: visit.id,
                      rating: Number(rating),
                      comment: String(values.comment ?? ""),
                    },
                    true,
                    "PUT",
                  );
                  setReviewing(false);
                  await refresh();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <label>
                Your rating
                <select
                  value={rating}
                  onChange={(e) => setRating(e.target.value)}
                >
                  {[5, 4, 3, 2, 1].map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
              </label>
              <textarea
                name="comment"
                maxLength={1000}
                placeholder="Your consultation experience (optional)"
              />
              <button disabled={busy}>Save rating</button>
            </form>
          )}
        </>
      )}
      {error && (
        <p role="alert" className="hs-error">
          {error}
        </p>
      )}
    </article>
  );
}

function SavedConsultationNotes({ records }: { records: SavedVisitNote[] }) {
  return records.length ? (
    <div className="dc-saved-history">
      <h2>Saved consultation notes</h2>
      <p className="hs-muted">Personal diary notes saved to this profile.</p>
      {records
        .slice()
        .sort((a, b) => b.date.localeCompare(a.date))
        .map((record) => (
          <article className="dc-visit" key={record.id}>
            <strong>{record.title}</strong>
            <small>
              {record.date}
              {record.doctor ? " ? " + record.doctor : ""}
            </small>
            {record.notes && <p>{record.notes}</p>}
            <span className="dc-status">Saved diary note</span>
          </article>
        ))}
    </div>
  ) : null;
}
