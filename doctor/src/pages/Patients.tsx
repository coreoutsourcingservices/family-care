import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import WorkspacePage, { ModuleBadge, PageSearch, PageStatus, useWorkspaceData } from '../components/WorkspacePage';
import { PatientName } from '../components/TableElements';
import { loadPatients } from '../lib/workspaceApi';

export default function Patients() {
  const { data, loading, error, refresh } = useWorkspaceData(loadPatients);
  const [params] = useSearchParams();
  const [search, setSearch] = useState(params.get('search') ?? '');
  useEffect(() => { setSearch(params.get('search') ?? ''); }, [params]);
  const [module, setModule] = useState('all');
  const filtered = data?.filter(patient => (module === 'all' || patient.module === module) && `${patient.full_name} ${patient.id}`.toLowerCase().includes(search.toLowerCase())) ?? [];
  return <WorkspacePage title="Patients" description="Family profiles connected to your doctor account, shared with permission." refresh={refresh}>
    <div className="dw-toolbar"><PageSearch value={search} onChange={setSearch} placeholder="Search connected patients" /><select aria-label="Care area" value={module} onChange={event => setModule(event.target.value)}><option value="all">All care areas</option><option value="child">Child Care</option><option value="women">Women’s Health</option><option value="adult">Adult Health</option></select><span>{loading ? 'Loading...' : `${filtered.length} profiles`}</span></div>
    <PageStatus loading={loading} error={error} empty={!filtered.length} emptyTitle={data?.length ? 'No matching patients' : 'No connected patients yet'}><div className="dw-panel dw-table-wrap"><table className="dw-table"><thead><tr><th>Patient</th><th>Care area</th><th>Date of birth</th><th>Guardian contact</th><th>Shared information</th></tr></thead><tbody>{filtered.map(patient => <tr key={patient.id}><td><PatientName name={patient.full_name} /></td><td><ModuleBadge module={patient.module} /></td><td>{patient.date_of_birth || 'Not provided'}</td><td>{patient.guardian_contact ? <a href={`tel:${patient.guardian_contact}`}>{patient.guardian_contact}</a> : 'Not provided'}</td><td><Link to={`/doctor/clinical-records?patient=${patient.id}`}>View records →</Link><Link to={`/doctor/reports?patient=${patient.id}`}>View reports →</Link></td></tr>)}</tbody></table></div></PageStatus>
  </WorkspacePage>;
}
