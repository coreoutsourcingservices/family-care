import { careApi } from '../../../app/src/lib/careApi';
export { careApi };
export type PatientProfile = { id: string; full_name: string; module: string; date_of_birth?: string; guardian_contact?: string; created_at?: string };
export type ConsultationRequest = { id: string; child_id: string; title: string; date: string; status: string; notes?: string; provider?: string; systolic?: number; diastolic?: number; pulse?: number; glucose?: number; total?: number; ldl?: number; hdl?: number; triglycerides?: number; minutes?: number; context?: string };
export type ClinicalRecord = { schedule_id?:string; category?:string; source_role?:string; author_id?:string; author_name?:string; id: string; title: string; kind: string; date: string; notes?: string; status?: string; weight?: string; height?: string; provider?: string; systolic?: number; diastolic?: number; pulse?: number; glucose?: number; total?: number; ldl?: number; hdl?: number; triglycerides?: number; minutes?: number; context?: string };
export type SharedReport = { id: string; profile_id: string; name: string; content_type?: string; created_at: string; size_bytes?: number };

export async function listAll<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  for (let page = 1; ; page++) {
    const data = await careApi<{ items: T[]; total: number }>(`${path}${path.includes('?') ? '&' : '?'}page=${page}&per_page=100`);
    result.push(...data.items);
    if (!data.items.length || result.length >= data.total || data.items.length < 100) return result;
  }
}

export const loadPatients = () => listAll<PatientProfile>('/doctors/care-profiles');
export const loadConsultations = () => listAll<ConsultationRequest>('/doctors/consultation-requests');
export const loadRecords = (id: string) => listAll<ClinicalRecord>(`/doctors/care-profiles/${id}/records`);
export const loadReports = (id: string) => listAll<SharedReport>(`/doctors/care-profiles/${id}/reports`);
