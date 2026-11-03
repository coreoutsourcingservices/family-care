import RecycleBin from '@/components/recycle-bin';
import {requireUser} from '@/lib/auth';

export default async function Page(){
  await requireUser('ADMIN');
  return <RecycleBin/>;
}
