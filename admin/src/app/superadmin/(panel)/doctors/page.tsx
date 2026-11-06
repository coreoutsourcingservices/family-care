import LocalizedText from '@/components/localized-text';
import {Suspense} from 'react';
import Directory from '@/components/directory';
export default function Page(){return <Suspense fallback={<p role="status"><LocalizedText text="Loading accounts…"/></p>}><Directory role="SUPERADMIN" kind="doctors"/></Suspense>;}