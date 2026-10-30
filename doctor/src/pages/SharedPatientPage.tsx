import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Download } from 'lucide-react';
import WorkspacePage, { PageSearch, PageStatus, useWorkspaceData } from '../components/WorkspacePage';
import { PatientName, RowActions } from '../components/TableElements';
import { loadPatients, loadRecords, loadReports } from '../lib/workspaceApi';
import { downloadReport } from '../../../app/src/lib/healthProfiles';

export default function SharedPatientPage({ mode }: { mode: 'records' | 'reports' | 'prescriptions' }) {
  const [params, setParams] = useSearchParams();
  const patients = useWorkspaceData(loadPatients);
  const patientId = params.get('patient') ?? '';
  const allowed = patients.data?.some(patient => patient.id === patientId) ?? false;
  const [search, setSearch] = useState('');
  const [type, setType] = useState('all');
  const [range, setRange] = useState('all');
  const [downloadError, setDownloadError] = useState('');
  const [downloading, setDownloading] = useState('');
  useEffect(() => {
    if (patients.data?.length && !allowed) setParams({ patient: patients.data[0].id }, { replace: true });
  }, [patients.data, allowed, setParams]);
  const records = useWorkspaceData(() => allowed && mode === 'records' ? loadRecords(patientId) : Promise.resolve([]), [allowed, patientId, mode]);
  const reports = useWorkspaceData(() => allowed && mode !== 'records' ? loadReports(patientId) : Promise.resolve([]), [allowed, patientId, mode]);
  const title = mode === 'records' ? 'Clinical Records' : mode === 'reports' ? 'Reports' : 'Prescriptions';
  const state = mode === 'records' ? records : reports;
  const recordRows = records.data?.filter(row => (type === 'all' || row.kind === type) && `${row.title} ${row.kind} ${row.notes ?? ''}`.toLowerCase().includes(search.toLowerCase())) ?? [];
  const reportRows = reports.data?.filter(row => (mode !== 'prescriptions' || /prescription|\brx\b/i.test(row.name)) && (type === 'all' || (row.content_type?.startsWith('image/') || /\.(png|jpe?g|webp)$/i.test(row.name) ? 'image' : /\.pdf$/i.test(row.name) ? 'pdf' : 'document') === type) && (range === 'all' || Date.now() - Date.parse(row.created_at) <= Number(range) * 86400000) && row.name.toLowerCase().includes(search.toLowerCase())) ?? [];
  const selectedName = patients.data?.find(patient => patient.id === patientId)?.full_name ?? 'Shared profile';
  return <WorkspacePage title={title} description={mode === 'records' ? 'Review family-reported clinical history shared with your practice.' : 'View original documents shared by connected families.'} refresh={() => { patients.refresh(); records.refresh(); reports.refresh(); }}>
    <div className="dw-toolbar"><select aria-label="Select patient" disabled={!patients.data?.length} value={allowed ? patientId : ''} onChange={event => { setParams({ patient: event.target.value }); setSearch(''); setDownloadError(''); }}><option value="" disabled>Select a patient</option>{patients.data?.map(patient => <option key={patient.id} value={patient.id}>{patient.full_name}</option>)}</select><PageSearch value={search} onChange={setSearch} placeholder={`Search ${title.toLowerCase()}`} /><select aria-label={mode === 'records' ? 'Record type' : 'Report type'} value={type} onChange={event => setType(event.target.value)}><option value="all">{mode === 'records' ? 'All record types' : 'All file types'}</option>{mode === 'records' ? [...new Set(records.data?.map(row => row.kind))].map(kind => <option key={kind} value={kind}>{kind.replaceAll('_', ' ')}</option>) : <><option value="pdf">PDF</option><option value="image">Image</option><option value="document">Other documents</option></>}</select>{mode !== 'records' && <select aria-label="Shared date range" value={range} onChange={event => setRange(event.target.value)}><option value="all">All time</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option></select>}</div>
    {mode === 'records' && <p className="dw-info">Entries are family-reported history. They are not doctor-authored diagnoses or prescriptions.</p>}
    {mode === 'prescriptions' && <p className="dw-info">Files with “prescription” or “Rx” in their name appear here. <Link to={`/doctor/reports?patient=${patientId}`}>Browse all shared reports</Link> for other filenames. Creating or issuing prescriptions is not available yet.</p>}
    {downloadError && <p className="dw-error" role="alert">{downloadError}</p>}
    <PageStatus loading={patients.loading || (allowed && state.loading)} error={patients.error || state.error} empty={!allowed || (mode === 'records' ? !recordRows.length : !reportRows.length)} emptyTitle={!patients.data?.length ? 'No connected patient profiles' : `No matching ${title.toLowerCase()}`}>
      {mode === 'records' ? <div className="dw-panel dw-table-wrap"><table className="dw-table"><thead><tr><th>Patient</th><th>Record type</th><th>Record / entry</th><th>Recorded on</th><th>Actions</th></tr></thead><tbody>{recordRows.map(row => <tr key={row.id}><td><PatientName name={selectedName} /></td><td><span className="dw-badge">{row.kind.replaceAll('_', ' ')}</span></td><td><h3 className="dw-row-title">{row.title}</h3><small className="dw-source">Family reported</small></td><td><time>{row.date}</time></td><td><RowActions label={row.title}><p className="dw-notes">{row.notes || 'No additional notes.'}</p>{row.status && <p>Status: {row.status}</p>}{row.weight && <p>Weight: {row.weight} kg</p>}{row.height && <p>Height: {row.height} cm</p>}{row.systolic != null && <p>Blood pressure: {row.systolic}/{row.diastolic} mmHg</p>}{row.pulse != null && <p>Pulse: {row.pulse} bpm</p>}{row.glucose != null && <p>Blood glucose: {row.glucose} mg/dL</p>}{(['total','ldl','hdl','triglycerides'] as const).map(key => row[key] != null && <p key={key}>{key.toUpperCase()}: {row[key]} mg/dL</p>)}{row.minutes != null && <p>Activity: {row.minutes} minutes</p>}{row.context && <p>{row.context}</p>}</RowActions></td></tr>)}</tbody></table></div> : <div className="dw-panel dw-table-wrap"><table className="dw-table"><thead><tr><th>Patient</th><th>{mode === 'prescriptions' ? 'File name' : 'Report name'}</th><th>Type</th><th>Shared on</th><th>Actions</th></tr></thead><tbody>{reportRows.map(report => <tr key={report.id}><td><PatientName name={selectedName} /></td><td><h3 className="dw-row-title">{report.name}</h3>{report.size_bytes !== undefined && <small>{Math.ceil(report.size_bytes / 1024)} KB</small>}</td><td><span className="dw-badge">{mode === 'prescriptions' ? 'Prescription file' : report.content_type?.startsWith('image/') || /\.(png|jpe?g|webp)$/i.test(report.name) ? 'Image' : /\.pdf$/i.test(report.name) ? 'PDF document' : 'Document'}</span></td><td><time>{report.created_at.slice(0, 10)}</time></td><td><RowActions label={report.name}><button className="dw-secondary" disabled={!!downloading} onClick={async () => { setDownloading(report.id); setDownloadError(''); try { await downloadReport({ id: report.id, name: report.name, addedAt: report.created_at, downloadPath: `/api/v1/doctors/care-profiles/${patientId}/reports/${report.id}/download` }); } catch (error) { setDownloadError(error instanceof Error ? error.message : 'Could not open this report.'); } finally { setDownloading(''); } }}><Download size={15} />{downloading === report.id ? 'Opening...' : 'Open original'}</button></RowActions></td></tr>)}</tbody></table></div>}

    </PageStatus>
  </WorkspacePage>;
}
