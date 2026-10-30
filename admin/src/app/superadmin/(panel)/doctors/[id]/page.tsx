import DoctorDetails from '@/components/doctor-details';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <DoctorDetails role="SUPERADMIN" id={id}/>;}
