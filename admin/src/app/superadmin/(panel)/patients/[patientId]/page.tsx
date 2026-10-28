import PatientDetails from '@/components/patient-details';
export default async function Page({params}:{params:Promise<{patientId:string}>}){const {patientId}=await params;return <PatientDetails role="SUPERADMIN" patientId={patientId}/>;}
