import Settings from '@/components/settings';
import {requireUser} from '@/lib/auth';
export default async function Page(){const user=await requireUser('ADMIN');return <Settings role="ADMIN" user={user}/>;}