import type { ReactNode } from 'react';
import { MoreHorizontal } from 'lucide-react';

export function PatientName({ name }: { name: string }) {
  return <span className="dw-patient-name"><span aria-hidden="true">{name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('')}</span><strong>{name}</strong></span>;
}
export function RowActions({ label, children }: { label: string; children: ReactNode }) {
  return <details className="dw-row-actions"><summary aria-label={`Actions for ${label}`}><MoreHorizontal size={19} /></summary><div>{children}</div></details>;
}
export function StatusBadge({ status }: { status?: string }) {
  const value = status || 'REQUESTED';
  return <span className={`dw-status-badge ${value.toLowerCase().replaceAll('_', '-')}`}>{value.replaceAll('_', ' ').toLowerCase()}</span>;
}
