import Dashboard from '@/components/dashboard';
import {requireUser} from '@/lib/auth';
export default async function Page(){const user=await requireUser('SUPERADMIN');return <Dashboard role="SUPERADMIN" user={user}/>;}