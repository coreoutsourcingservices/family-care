import { useEffect, useMemo, useRef } from 'react';
import Chart from 'chart.js/auto';
import type { ChartConfiguration, ChartType } from 'chart.js';
import type { ConsultationRequest, PatientProfile } from '../lib/workspaceApi';

function ChartCard({ title, description, type, labels, values, locked = false }: { title: string; description: string; type: ChartType; labels: string[]; values: number[]; locked?: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const hasData = values.some(value => value > 0);
  useEffect(() => {
    if (!canvas.current || !hasData || locked) return;
    const doughnut = type === 'doughnut';
    const chart = new Chart(canvas.current, {
      type, data: { labels, datasets: [{ label: title, data: values, borderColor: type === 'line' ? '#ae55e7' : '#fff', borderWidth: type === 'line' ? 2 : 3,
        backgroundColor: type === 'line' ? '#dcb6f63d' : ['#ad63e5', '#f18bcc', '#8d99ec', '#b99ae9', '#ffc6db'],
        ...(type === 'line' ? { fill: true, tension: .35, pointRadius: 4, pointBackgroundColor: '#b46ade' } : {}),
        ...(type === 'bar' ? { borderRadius: 9, maxBarThickness: 45 } : {}),
      }] },
      options: { responsive: true, maintainAspectRatio: false, animation: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 400 },
        plugins: { legend: { display: doughnut, position: 'bottom', labels: { color: '#937aa4', usePointStyle: true, padding: 18, font: { size: 10 } } } },
        ...(doughnut ? { cutout: '70%' } : { scales: { x: { grid: { display: false }, ticks: { color: '#a38aaf', font: { size: 10 } } }, y: { beginAtZero: true, ticks: { precision: 0, color: '#a38aaf', font: { size: 10 } }, grid: { color: '#f0e7f8' } } } }),
      },
    } as ChartConfiguration);
    return () => chart.destroy();
  }, [type, labels, values, title, hasData, locked]);
  return <article className="dw-panel doctor-chart-card"><h3>{title}</h3><p>{description}</p><div className="doctor-chart-canvas">{hasData && !locked ? <canvas ref={canvas} role="img" aria-label={`${title}: ${labels.map((label, index) => `${label} ${values[index]}`).join(', ')}`} /> : <div className="doctor-chart-empty"><span aria-hidden="true">▥</span><strong>{locked ? 'Available after approval' : 'No chart data yet'}</strong><small>{locked ? 'Your practice insights will appear here.' : 'Charts update when your account receives real data.'}</small></div>}</div><details className="doctor-chart-data"><summary>View chart data</summary><ul>{labels.map((label, index) => <li key={label}><span>{label}</span><strong>{locked ? '—' : values[index]}</strong></li>)}</ul></details></article>;
}

export default function DashboardCharts({ patients = [], requests = [], locked = false, loading = false, error = '' }: { patients?: PatientProfile[]; requests?: ConsultationRequest[]; locked?: boolean; loading?: boolean; error?: string }) {
  const charts = useMemo(() => {
    const current = new Date();
    const months = Array.from({ length: 6 }, (_, index) => new Date(current.getFullYear(), current.getMonth() - 5 + index, 1));
    const labels = months.map(date => date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' }));
    const monthly = months.map(date => patients.filter(patient => patient.created_at && new Date(patient.created_at).getFullYear() === date.getFullYear() && new Date(patient.created_at).getMonth() === date.getMonth()).length);
    const areaValues = ['child', 'women', 'adult'].map(module => patients.filter(patient => patient.module === module).length);
    const statuses = [...new Set(requests.map(request => request.status || 'REQUESTED'))].sort();
    return { labels, monthly, areas: ['Child Care', 'Women’s Health', 'Adult Health'], areaValues, statuses: statuses.length ? statuses : ['REQUESTED'], statusValues: statuses.length ? statuses.map(status => requests.filter(request => (request.status || 'REQUESTED') === status).length) : [0] };
  }, [patients, requests]);
  if (loading) return <p className="dw-panel" role="status">Loading practice charts...</p>;
  if (error) return <p className="dw-error" role="alert">Practice charts could not load. Refresh the dashboard to try again.</p>;
  return <section className="doctor-dashboard-insights" aria-label="Practice charts"><div className="dw-panel-title"><h3>Practice insights</h3><small>Live account data · no sample readings</small></div><div className="doctor-charts-grid"><ChartCard title="Family connections" description="New connected profiles by month · last 6 months" type="line" labels={charts.labels} values={charts.monthly} locked={locked} /><ChartCard title="Care areas" description="Your connected family profiles by care module" type="doughnut" labels={charts.areas} values={charts.areaValues} locked={locked} /><ChartCard title="Consultation requests" description="Requests grouped by their recorded status" type="bar" labels={charts.statuses} values={charts.statusValues} locked={locked} /></div></section>;
}
