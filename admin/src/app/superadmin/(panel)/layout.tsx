import { requireUser } from '@/lib/auth';
import Shell from '@/components/shell';
export default async function Layout({children}:{children:React.ReactNode}){const user=await requireUser('SUPERADMIN');return <Shell role="SUPERADMIN" user={user}>{children}</Shell>;}
