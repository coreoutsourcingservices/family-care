import DoctorDetails from '@/components/doctor-details';
export default async function Page({params}:{params:Promise<{id:string;familyId:string}>}){const {id,familyId}=await params;return <DoctorDetails role="ADMIN" id={id} familyId={familyId}/>;}
