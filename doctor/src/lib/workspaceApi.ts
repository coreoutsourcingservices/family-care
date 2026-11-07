import { careApi } from "../../../app/src/lib/careApi";
export { careApi };
export type PatientProfile = {
  workspacePath?: string;
  id: string;
  full_name: string;
  module: string;
  date_of_birth?: string;
  guardian_contact?: string;
  created_at?: string;
};
export type ConsultationRequest = {
  id: string;
  child_id: string;
  title: string;
  date: string;
  status: string;
  notes?: string;
  provider?: string;
  systolic?: number;
  diastolic?: number;
  pulse?: number;
  glucose?: number;
  total?: number;
  ldl?: number;
  hdl?: number;
  triglycerides?: number;
  minutes?: number;
  context?: string;
};
export type ClinicalRecord = {
  schedule_id?: string;
  category?: string;
  source_role?: string;
  author_id?: string;
  author_name?: string;
  id: string;
  title: string;
  kind: string;
  date: string;
  notes?: string;
  status?: string;
  weight?: string;
  height?: string;
  provider?: string;
  systolic?: number;
  diastolic?: number;
  pulse?: number;
  glucose?: number;
  total?: number;
  ldl?: number;
  hdl?: number;
  triglycerides?: number;
  minutes?: number;
  context?: string;
};
export type SharedReport = {
  downloadPath?: string;
  category?: string;
  category_reviewed?: boolean;
  id: string;
  profile_id: string;
  name: string;
  content_type?: string;
  created_at: string;
  size_bytes?: number;
};

export async function listAll<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  for (let page = 1; ; page++) {
    const data = await careApi<{ items: T[]; total: number }>(
      `${path}${path.includes("?") ? "&" : "?"}page=${page}&per_page=100`,
    );
    result.push(...data.items);
    if (
      !data.items.length ||
      result.length >= data.total ||
      data.items.length < 100
    )
      return result;
  }
}

export const loadPatients = () =>
  listAll<PatientProfile>("/doctors/care-profiles");
export const loadConsultations = () =>
  listAll<ConsultationRequest>("/doctors/consultation-requests");
export const loadRecords = (id: string) =>
  listAll<ClinicalRecord>(`/doctors/care-profiles/${id}/records`);
export const loadReports = (id: string) =>
  listAll<SharedReport>(`/doctors/care-profiles/${id}/reports`);

// Shared Adult/Women tabs have separate, permission-scoped APIs.
export async function loadPatientRoster(): Promise<PatientProfile[]> {
  const [regular, women, adult] = await Promise.all([
    loadPatients(),
    careApi<{ items: { id: string; name: string }[] }>("/women/shared"),
    careApi<{ items: { id: string; name: string }[] }>("/adult-access/shared"),
  ]);
  const roster = new Map(regular.map((p) => [p.id, p]));
  for (const [module, items] of [
    ["women", women.items],
    ["adult", adult.items],
  ] as const)
    for (const p of items)
      roster.set(p.id, {
        ...roster.get(p.id),
        id: p.id,
        full_name: p.name,
        module,
        workspacePath: "/doctor/" + module + "/" + p.id,
      });
  return [...roster.values()];
}
export async function loadVisibleRecords(
  patient: PatientProfile,
): Promise<ClinicalRecord[]> {
  if (!patient.workspacePath) return loadRecords(patient.id);
  const prefix = patient.module === "women" ? "/women" : "/adult-access";
  const result = await careApi<{
    records: (ClinicalRecord & { section?: string })[];
  }>(`${prefix}/profiles/${patient.id}/workspace`);
  return result.records.map((r) => ({
    ...r,
    kind: r.kind || r.section || "history",
  }));
}
export async function loadVisibleReports(
  patient: PatientProfile,
): Promise<SharedReport[]> {
  if (!patient.workspacePath) return loadReports(patient.id);
  const prefix = patient.module === "women" ? "/women" : "/adult-access";
  const base = `${prefix}/profiles/${patient.id}/reports`;
  return (await listAll<SharedReport>(base)).map((r) => ({
    ...r,
    profile_id: patient.id,
    downloadPath: `/api/v1${base}/${r.id}/download`,
  }));
}
