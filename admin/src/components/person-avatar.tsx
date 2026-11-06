'use client';

import {useState} from 'react';

export function PersonAvatar({name,photoUrl}:{name:string;photoUrl?:string|null}){
 const [failedUrl,setFailedUrl]=useState<string>();
 const initial=Array.from(name.trim())[0]?.toLocaleUpperCase()||'?';
 return <span className="person-avatar" role="img" aria-label={`${name} profile picture`}>
  {photoUrl&&photoUrl!==failedUrl?<img src={photoUrl} alt="" onError={()=>setFailedUrl(photoUrl)}/>:initial}
 </span>;
}
