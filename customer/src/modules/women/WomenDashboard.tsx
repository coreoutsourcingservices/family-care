import CareGuidanceLayout from "../../../../app/src/components/CareGuidance";
import {
  CustomerLanguageSelector,
  useCustomerLanguage,
} from "../../localization/CustomerLanguage";
import CustomerNotes from "../../../../app/src/components/CustomerNotes";
import PregnancyCareGuide from "./PregnancyCareGuide";
import ProfilePlanner from "../../components/ProfilePlanner";
import DoctorConsultation from "../../../../app/src/components/DoctorConsultation";

import { ImportedReportRecords } from "../../../../app/src/components/ReportRecordReview";
import ProfileDoctorConnection from "./WomenDoctorConnection";
import WomenSharing from "./WomenSharing";

import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate, useParams } from "react-router-dom";
import {
  Heart,
  LayoutDashboard,
  CalendarDays,
  Activity,
  Flower2,
  Baby,
  Sprout,
  ShieldCheck,
  FileText,
  Stethoscope,
  Settings,
  ArrowLeft,
  Menu,
  X,
  Plus,
  LogOut,
  ChevronDown,
  Bell,
  Search,
} from "lucide-react";
import { gsap } from "gsap";
import WomenCalendar from "./WomenCalendar";
import { authApi, ApiError } from "../../../../app/src/lib/authApi";
import {
  loadProfiles,
  loadProfile,
  type HealthProfile,
} from "../../../../app/src/lib/healthProfiles";
import CustomerDashboard from "../../../../app/src/pages/CustomerDashboard";
import { WomenDiary, WomenOverview, WomenReports } from "./WomenPages";
import { womenPages, useWomenRecords, today } from "./womenRecords";
import "../../../../app/src/pages/customer-dashboard.css";
const icons = [
  LayoutDashboard,
  Heart,
  CalendarDays,
  Activity,
  Baby,
  Flower2,
  Heart,
  Sprout,
  ShieldCheck,
  FileText,
  Stethoscope,
  Settings,
];
export default function WomenDashboard() {
  const {t}=useCustomerLanguage();
  const { "*": path = "" } = useParams();
  const section = path || "dashboard";
  const navigate = useNavigate();
  const [profile, setProfile] = useState<HealthProfile>(),
    [profiles, setProfiles] = useState<HealthProfile[]>([]),
    [owner, setOwner] = useState(""),
    [error, setError] = useState(""),
    [attempt, setAttempt] = useState(0),
    [loaded, setLoaded] = useState(false);
  const adding = new URLSearchParams(window.location.search).get("add") === "1";
  useEffect(() => {
    let current = true;
    setError("");
    (async () => {
      const [session, list] = await Promise.all([
        authApi("/patients/me", undefined, "GET"),
        loadProfiles("", "women"),
      ]);
      if (!current) return;
      if (session.user?.role !== "PATIENT") {
        navigate("/customer/login", { replace: true });
        return;
      }
      const key = "familycare.selectedWoman." + session.user.id;
      const selected =
        list.find(
          (p) =>
            p.id ===
            (new URLSearchParams(location.search).get("profile") ||
              sessionStorage.getItem(key)),
        ) ?? list[0];
      setOwner(session.user.id);
      setProfiles(list);
      setProfile(selected);
      if (selected) sessionStorage.setItem(key, selected.id);
      setLoaded(true);
    })().catch((e) => {
      if (!current) return;
      if (e instanceof ApiError && [401, 403].includes(e.status))
        navigate("/customer/login", { replace: true });
      else
        setError(
          e instanceof Error ? e.message : "Could not load Women’s Health.",
        );
    });
    return () => {
      current = false;
    };
  }, [attempt, adding]);
  if (error && !profile)
    return (
      <div className="ch-loading">
        <Heart />
        <p role="alert">{error}</p>
        <button onClick={() => setAttempt((n) => n + 1)}>Try again</button>
        <Link to="/customer/dashboard">{t("Family overview")}</Link>
      </div>
    );
  if (!loaded)
    return (
      <div className="ch-loading" role="status">
        <Heart />
        <p>Opening your wellbeing space…</p>
      </div>
    );
  if (adding || !profile) return <CustomerDashboard module="women" />;
  return (
    <WomenSpace
      key={profile.id}
      section={section}
      owner={owner}
      profile={profile}
      profiles={profiles}
      onSwitch={(id) => {
        const next = profiles.find((p) => p.id === id);
        if (next) {
          sessionStorage.setItem("familycare.selectedWoman." + owner, id);
          setProfile(next);
          navigate("/customer/women/dashboard");
        }
      }}
      onRefresh={async () => setProfile(await loadProfile(profile.id))}
    />
  );
}
function WomenSpace({
  section,
  owner,
  profile,
  profiles,
  onSwitch,
  onRefresh,
}: {
  section: string;
  owner: string;
  profile: HealthProfile;
  profiles: HealthProfile[];
  onSwitch: (id: string) => void;
  onRefresh: () => Promise<void>;
}) {
  const { t, direction } = useCustomerLanguage();
  const store = useWomenRecords(owner, profile.id);
  const [menu, setMenu] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const root = useRef<HTMLDivElement>(null);
  const [calendar, setCalendar] = useState(false);
  const [search, setSearch] = useState("");
  useEffect(() => {
    setCalendar(false);
    setSearch("");
  }, [section]);
  const due = store.records.filter(
    (record) =>
      record.section === "reminder" &&
      record.status === "Planned" &&
      record.date <= today(),
  );
  useEffect(() => {
    setMenu(false);
    const media = gsap.matchMedia();
    media.add("(prefers-reduced-motion: no-preference)", () => {
      const context = gsap.context(() => {
        gsap.from(
          ".ch-content > .wh-hero, .ch-content > .ch-panel, .wh-shortcuts > a",
          {
            y: 12,
            opacity: 0,
            duration: 0.35,
            stagger: 0.035,
            clearProps: "all",
          },
        );
      }, root);
      return () => context.revert();
    });
    return () => media.revert();
  }, [section]);
  useEffect(() => {
    const media = gsap.matchMedia();
    media.add(
      "(hover: hover) and (prefers-reduced-motion: no-preference)",
      () => {
        const node = root.current;
        if (!node) return;
        const selector =
          ".wh-ref-explore > a, .wh-ref-stats > a, .wh-task, .ch-sidebar nav a, .wh-ref-hero .ch-button";
        const targets = new Set<HTMLElement>();
        const over = (event: PointerEvent) => {
          const target = (event.target as HTMLElement).closest<HTMLElement>(
            selector,
          );
          if (!target || target.contains(event.relatedTarget as Node | null))
            return;
          targets.add(target);
          gsap.to(target, { y: -3, duration: 0.2, overwrite: "auto" });
          const text = target.querySelector("strong");
          if (text) gsap.to(text, { color: "#e82e79", duration: 0.2 });
        };
        const out = (event: PointerEvent) => {
          const target = (event.target as HTMLElement).closest<HTMLElement>(
            selector,
          );
          if (!target || target.contains(event.relatedTarget as Node | null))
            return;
          gsap.to(target, {
            y: 0,
            duration: 0.2,
            overwrite: "auto",
            clearProps: "transform",
          });
          const text = target.querySelector("strong");
          if (text) gsap.to(text, { clearProps: "color", duration: 0.2 });
        };
        node.addEventListener("pointerover", over);
        node.addEventListener("pointerout", out);
        return () => {
          node.removeEventListener("pointerover", over);
          node.removeEventListener("pointerout", out);
          targets.forEach((target) => {
            gsap.killTweensOf(target);
            gsap.set(target, { clearProps: "transform" });
            const text = target.querySelector("strong");
            if (text) {
              gsap.killTweensOf(text);
              gsap.set(text, { clearProps: "color" });
            }
          });
        };
      },
    );
    return () => media.revert();
  }, []);
  useEffect(() => {
    const sidebar = root.current?.querySelector<HTMLElement>(".ch-sidebar");
    if (!sidebar) return;
    const media = window.matchMedia("(max-width:700px)");
    const sync = () => {
      sidebar.inert = media.matches && !menu;
    };
    sync();
    media.addEventListener("change", sync);
    if (menu)
      sidebar.querySelector<HTMLButtonElement>(".ch-close-menu")?.focus();
    return () => {
      media.removeEventListener("change", sync);
      sidebar.inert = false;
    };
  }, [menu]);
  useEffect(() => {
    if (!menu) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(false);
    };
    document.addEventListener("keydown", close);
    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener("keydown", close);
    };
  }, [menu]);
  const brand = (
    <Link to="/customer/dashboard" className="ch-brand">
      <Flower2 />
      <span>
        <strong>FamilyCare+</strong>
        <small>Every phase matters</small>
      </span>
    </Link>
  );
  return (
    <div className="ch-app wh-app" ref={root} dir={direction}>
      <aside
        className={"ch-sidebar " + (menu ? "is-open" : "")}
        aria-label="Women's Health sidebar"
      >
        <div className="ch-sidebar-logo">
          {brand}
          <button
            className="ch-icon-button ch-close-menu"
            onClick={() => setMenu(false)}
            aria-label="Close navigation"
          >
            <X />
          </button>
        </div>
        <Link className="ch-back-family" to="/customer/dashboard">
          <ArrowLeft size={15} />
          {profile.profileType === "self"
            ? "Family dashboard"
            : "Family overview"}
        </Link>
        <button
          className="wh-calendar-launch"
          onClick={() => {
            setMenu(false);
            setCalendar(true);
          }}
        >
          <CalendarDays size={18} />
          <span>{t("Calendar & reminders")}</span>
          {due.length > 0 && <b>{due.length}</b>}
        </button>
        <Link className="ch-back-family" to="/customer/women/shared">
          {t("Shared with me")}
        </Link>
        <span className="ch-nav-label">WOMEN’S HEALTH</span>
        <nav aria-label="Women's health navigation">
          {womenPages.map(([id, label], i) => {
            if (profile.profileType === "self" && id === "settings")
              return null;
            const Icon = icons[i] ?? ShieldCheck;
            return (
              <NavLink key={id} to={"/customer/women/" + id}>
                <Icon size={17} />
                {t(label)}
              </NavLink>
            );
          })}
          {profile.profileType === "self" && (
            <>
              <span className="ch-nav-label">MY ACCOUNT</span>
              <Link to="/customer/dashboard?action=add-member">
                <Plus size={17} />
                {t("Add member")}
              </Link>
              <NavLink to="/customer/women/notes">
                <FileText size={17} />
                {t("Add notes")}
              </NavLink>
              <NavLink to="/customer/women/settings">
                <Settings size={17} />
                {t("Settings")}
              </NavLink>
            </>
          )}
          <NavLink to="/customer/women/sharing">
            <ShieldCheck size={17} />
            Access &amp; Sharing
          </NavLink>
        </nav>
        <div className="ch-sidebar-bottom">
          <div className="ch-sidebar-profile">
            <Heart />
            <div>
              <strong>{profile.name}</strong>
              <small>Your wellbeing space</small>
            </div>
          </div>
          <button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await authApi("/auth/logout");
                navigate("/customer/login", { replace: true });
              } catch (e) {
                setError(
                  e instanceof Error ? e.message : "Could not sign out.",
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            <LogOut size={16} />
            {busy ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </aside>
      {menu && (
        <button
          className="ch-menu-overlay"
          aria-label="Close navigation overlay"
          onClick={() => setMenu(false)}
        />
      )}
      <div className="ch-main">
        <header className="ch-topbar">
          <div className="ch-mobile-brand">{brand}</div>
          <button
            className="ch-icon-button ch-open-menu"
            aria-label="Open women navigation"
            aria-expanded={menu}
            onClick={() => setMenu(!menu)}
          >
            <Menu />
          </button>
          <div className="wh-header-title">
            <strong>
              {womenPages.find(([id]) => id === section)?.[1] ??
                "Women’s Health"}
            </strong>
            <small>Your health journey, beautifully organised.</small>
          </div>
          <div
            className="wh-ref-search"
            onBlur={(event) => {
              if (
                !event.currentTarget.contains(
                  event.relatedTarget as Node | null,
                )
              )
                setSearch("");
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") setSearch("");
            }}
          >
            <Search size={16} />
            <input
              aria-label="Search women health"
              placeholder="Search anything?"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <div className="wh-ref-search-results">
                {womenPages
                  .filter(([, label]) =>
                    label.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map(([id, label]) => (
                    <Link
                      key={id}
                      to={"/customer/women/" + id}
                      onClick={() => setSearch("")}
                    >
                      {label}
                    </Link>
                  ))}
                {!womenPages.some(([, label]) =>
                  label.toLowerCase().includes(search.toLowerCase()),
                ) && <p>No matching pages</p>}
              </div>
            )}
          </div>
          <div className="ch-top-actions">
            <CustomerLanguageSelector compact />
            <Link className="wh-home" to="/customer/dashboard">
              <ArrowLeft size={16} />
              My family
            </Link>
            <label className="ch-child-select">
              <span className="sr-only">Switch women's profile</span>
              <select
                value={profile.id}
                onChange={(e) => onSwitch(e.target.value)}
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} />
            </label>
            <Link className="ch-button wh-add" to="/customer/women?add=1">
              <Plus size={16} />
              <span>Add profile</span>
            </Link>
            <button
              className="ch-icon-button wh-notification-button"
              aria-label={
                "Open notifications" +
                (due.length ? " (" + due.length + " due)" : "")
              }
              onClick={() => setCalendar(true)}
            >
              <Bell size={18} />
              {due.length > 0 && <b>{due.length}</b>}
            </button>
          </div>
        </header>
        <main className="ch-content">
          <CareGuidanceLayout
            module="women"
            section={section}
            profileId={profile.id}
          >
            <p className="ch-device-note">
              <ShieldCheck size={14} />
              Your diary and reports are saved to your account. You choose which
              tabs to share.
            </p>
            {(store.error || error) && (
              <p role="alert">{store.error || error}</p>
            )}
            {section === "notes" && profile.profileType === "self" ? (
              <CustomerNotes />
            ) : section === "planner" ? (
              <ProfilePlanner key={profile.id} profileId={profile.id} />
            ) : section === "sharing" ? (
              <WomenSharing profileId={profile.id} />
            ) : section === "consultation" ? (
              <DoctorConsultation
                profile={profile}
                history={store.records.filter(
                  (record) => record.section === "consultation",
                )}
              />
            ) : section === "dashboard" ? (
              <WomenOverview
                profile={profile}
                records={store.records}
                onAdd={store.add}
                onCalendar={() => setCalendar(true)}
              />
            ) : section === "records" ? (
              <WomenReports profile={profile} onRefresh={onRefresh} />
            ) : section === "settings" ? (
              <section className="ch-panel">
                <h1>Your profile</h1>
                <Link className="ch-button" to="/customer/women/sharing">
                  Access &amp; Sharing
                </Link>
                <h2>{profile.name}</h2>
                <p>Date of birth: {profile.dob || "Not recorded"}</p>
                <p>
                  Guardian contact: {profile.guardianContact || "Not recorded"}
                </p>
                <button
                  className="ch-button"
                  onClick={() => {
                    const url = URL.createObjectURL(
                      new Blob([JSON.stringify(store.records, null, 2)], {
                        type: "application/json",
                      }),
                    );
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "womens-health-diary.json";
                    a.click();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                  }}
                >
                  Download diary
                </button>
                <p>Export includes your account diary records.</p>
              </section>
            ) : womenPages.some(([id]) => id === section) ? (
              <>
                {section === "consultation" && (
                  <>
                    <ProfileDoctorConnection
                      profile={profile}
                      onRefresh={onRefresh}
                    />
                    <Link className="ch-button" to="/customer/women/sharing">
                      Access &amp; Sharing
                    </Link>
                  </>
                )}
                {section === "pregnancy" && (
                  <PregnancyCareGuide
                    key={profile.id}
                    profileId={profile.id}
                    owner={Boolean(store.workspace?.owner)}
                  />
                )}
                <ImportedReportRecords
                  profileId={profile.id}
                  kind={
                    section === "nutrition"
                      ? "growth,nutrition"
                      : section === "screening"
                        ? "vaccination"
                        : section === "health"
                          ? "history"
                          : section === "records"
                            ? undefined
                            : "__none"
                  }
                />
                <WomenDiary key={section} section={section} store={store} />
              </>
            ) : (
              <section className="ch-panel">
                <h1>Page not found</h1>
                <Link to="/customer/women/dashboard">Back to dashboard</Link>
              </section>
            )}
          </CareGuidanceLayout>
          <footer className="ch-footer">
            A little care, through every chapter.
          </footer>
        </main>
        <nav className="ch-mobile-nav" aria-label="Women quick navigation">
          {womenPages
            .filter(([id]) =>
              ["dashboard", "cycle", "records", "consultation"].includes(id),
            )
            .map(([id, label]) => (
              <NavLink key={id} to={"/customer/women/" + id}>
                <Heart size={18} />
                <span>
                  {id === "dashboard"
                    ? "Home"
                    : id === "consultation"
                      ? "Doctor"
                      : id === "records"
                        ? "Reports"
                        : label}
                </span>
              </NavLink>
            ))}
          <button onClick={() => setMenu(true)}>
            <Menu size={18} />
            More
          </button>
        </nav>
      </div>
      <WomenCalendar
        open={calendar}
        onClose={() => setCalendar(false)}
        records={store.records}
        onAdd={store.add}
        onRemove={store.remove}
      />
    </div>
  );
}
