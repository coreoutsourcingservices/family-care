import {useEffect,useState} from 'react';
import {authApi} from '../lib/authApi';
import {careApi} from '../lib/careApi';
export default function FamilyAccess({profileId}:{profileId:string}){
 const [enabled,setEnabled]=useState<boolean>(),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{let active=true;authApi('/patients/me',undefined,'GET').then(async session=>{if(session.user?.is_family_member&&session.user.member_profile_id===profileId){const data=await careApi<{enabled:boolean}>(`/patients/profiles/${profileId}/family-access`);if(active)setEnabled(data.enabled);}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[profileId]);
 if(enabled===undefined)return error?<p role="alert">{error}</p>:null;
 return <section className="fh-card"><h2>Family access</h2><p>Your medical details are private until you allow your inviting family to view them. This permission allows viewing only. You can revoke it anytime.</p><button className="fh-button" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{const data=await careApi<{enabled:boolean}>(`/patients/profiles/${profileId}/family-access`,{enabled:!enabled},true,'PUT');setEnabled(data.enabled);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>{busy?'Saving...':enabled?'Revoke family access':'Allow family to view my records'}</button>{error&&<p role="alert">{error}</p>}</section>;
}
