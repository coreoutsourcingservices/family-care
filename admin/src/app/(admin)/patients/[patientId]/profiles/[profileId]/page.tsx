import PatientDetails from '@/components/patient-details';
export default async function Page({params}:{params:Promise<{patientId:string;profileId:string}>}){const {patientId,profileId}=await params;return <PatientDetails role="ADMIN" patientId={patientId} profileId={profileId}/>;}
