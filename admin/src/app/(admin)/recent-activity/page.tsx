import RecentActivity from '@/components/recent-activity';
import {requireUser} from '@/lib/auth';

export default async function Page(){
  await requireUser('ADMIN');
  return <RecentActivity/>;
}
