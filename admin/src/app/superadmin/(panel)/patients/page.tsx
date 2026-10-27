import {Suspense} from 'react';
import Directory from '@/components/directory';
export default function Page(){return <Suspense fallback={<p>Loading accounts?</p>}><Directory role="SUPERADMIN" kind="patients"/></Suspense>;}