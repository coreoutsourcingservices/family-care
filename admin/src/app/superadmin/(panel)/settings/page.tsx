import Settings from '@/components/settings';
import {requireUser} from '@/lib/auth';
export default async function Page(){const user=await requireUser('SUPERADMIN');return <Settings role="SUPERADMIN" user={user}/>;}