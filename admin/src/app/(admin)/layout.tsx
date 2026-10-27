import { requireUser } from '@/lib/auth';
import Shell from '@/components/shell';
export default async function Layout({children}:{children:React.ReactNode}){const user=await requireUser('ADMIN');return <Shell role="ADMIN" user={user}>{children}</Shell>;}
