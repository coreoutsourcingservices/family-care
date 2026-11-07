import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import {
  CalendarDays,
  FileText,
  FolderHeart,
  Search,
  Stethoscope,
  Users,
} from "lucide-react";
import { getDoctorWorkspace } from "../onboarding/setupSession";
import { ApiError } from "../../../app/src/lib/authApi";
import DoctorWorkspaceLayout from "./DoctorWorkspaceLayout";

// Memory only: never persist clinical data in browser storage.
const workspaceCache = new Map<string, unknown>();
let cacheGeneration = 0;
window.addEventListener("familycare:doctor-cache-clear", () => {
  workspaceCache.clear();
  cacheGeneration++;
});

export function useWorkspaceData<T>(
  resource: string,
  load: () => Promise<T>,
  dependencies: unknown[] = [],
) {
  const key = JSON.stringify([
    getDoctorWorkspace()?.user.id,
    resource,
    dependencies,
  ]);
  const [result, setResult] = useState<{
    key: string;
    data?: T;
    error: string;
  }>(() => ({
    key,
    data: workspaceCache.get(key) as T | undefined,
    error: "",
  }));
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    const generation = cacheGeneration;
    let running = false;
    const update = async () => {
      if (running) return;
      running = true;
      try {
        const value = await load();
        if (active && generation === cacheGeneration) {
          workspaceCache.set(key, value);
          if (workspaceCache.size > 100)
            workspaceCache.delete(workspaceCache.keys().next().value!);
          setResult({ key, data: value, error: "" });
        }
      } catch (failure) {
        if (active && generation === cacheGeneration) {
          // Do not retain records after permission/session failures.
          const denied =
            failure instanceof ApiError &&
            [401, 403, 404].includes(failure.status);
          if (denied) workspaceCache.delete(key);
          setResult((previous) => ({
            key,
            data: denied
              ? undefined
              : previous.key === key
                ? previous.data
                : (workspaceCache.get(key) as T | undefined),
            error:
              failure instanceof Error
                ? failure.message
                : "Could not load this page.",
          }));
        }
      } finally {
        running = false;
      }
    };
    void update();
    const refresh = () => {
      if (!document.hidden) void update();
    };
    const interval = window.setInterval(refresh, 30000);
    window.addEventListener("focus", refresh);
    window.addEventListener("familycare:care-updated", refresh);
    return () => {
      active = false;
      clearInterval(interval);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("familycare:care-updated", refresh);
    };
  }, [key, attempt]);
  const data =
    result.key === key
      ? result.data
      : (workspaceCache.get(key) as T | undefined);
  const error = result.key === key ? result.error : "";
  return {
    data,
    error,
    loading: data === undefined && !error,
    refresh: () => setAttempt((value) => value + 1),
  };
}

export default function WorkspacePage({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
  refresh?: () => void;
}) {
  return (
    <DoctorWorkspaceLayout>
      <div className="dw-page-heading">
        <div>
          <span className="doctor-home-label">YOUR PRACTICE</span>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      {children}
    </DoctorWorkspaceLayout>
  );
}
export function PageStatus({
  loading,
  error,
  empty,
  emptyTitle = "Nothing here yet",
  children,
}: {
  loading: boolean;
  error: string;
  empty?: boolean;
  emptyTitle?: string;
  children?: ReactNode;
}) {
  if (loading)
    return (
      <div className="dw-panel dw-empty" role="status">
        Loading your workspace...
      </div>
    );
  if (error)
    return (
      <div className="dw-panel dw-error" role="alert">
        {error}
      </div>
    );
  if (empty) {
    const label = emptyTitle.toLowerCase();
    const Icon = label.includes("patient")
      ? Users
      : label.includes("consultation")
        ? Stethoscope
        : label.includes("dates")
          ? CalendarDays
          : label.includes("prescription")
            ? FileText
            : FolderHeart;
    return (
      <div className="dw-panel dw-empty">
        <div className="dw-empty-visual" aria-hidden="true">
          <span />
          <div>
            <Icon size={32} strokeWidth={1.5} />
          </div>
          <i />
        </div>
        <h3>{emptyTitle}</h3>
        <p>Shared information will appear here when it becomes available.</p>
      </div>
    );
  }
  return <>{children}</>;
}
export function PageSearch({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="dw-search">
      <Search size={17} />
      <input
        aria-label={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}
export function ModuleBadge({ module }: { module: string }) {
  return (
    <span className={`dw-badge ${module}`}>
      {module === "child"
        ? "Child Care"
        : module === "women"
          ? "Women’s Health"
          : "Adult Health"}
    </span>
  );
}
