import {useState,type FormEvent} from 'react';
import {careApi} from '../../../../app/src/lib/careApi';
import type {HealthProfile} from '../../../../app/src/lib/healthProfiles';
export default function WomenDoctorConnection({profile,onRefresh}:{profile:HealthProfile;onRefresh:()=>Promise<void>}){
 const [code,setCode]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function connect(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{await careApi('/patients/profiles/'+profile.id+'/connect-doctor',{referral_id:code.trim()});await onRefresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <section className="wh-sharing ch-panel"><h2>Connected doctor</h2>{profile.referral.doctor?<><p>{profile.referral.doctor.name}</p><button disabled={busy} onClick={async()=>{if(!confirm('Disconnect this doctor and end their access?'))return;setBusy(true);try{await careApi('/patients/profiles/'+profile.id+'/doctor',undefined,true,'DELETE');await onRefresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>Disconnect doctor</button></>:<form onSubmit={connect}><label>Doctor referral ID<input type="text" required maxLength={160} value={code} onChange={e=>setCode(e.target.value)}/></label><button className="ch-button" disabled={busy}>{busy?'Connecting…':'Connect doctor'}</button></form>}<p>Use Family & doctor access below to select tabs, permissions and expiry.</p>{error&&<p role="alert">{error}</p>}</section>;
}
