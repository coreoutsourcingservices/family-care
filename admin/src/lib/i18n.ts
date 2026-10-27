'use client';
import {useSyncExternalStore} from 'react';
import {useTranslation} from 'react-i18next';
const subscribe=()=>()=>{};
const clientSnapshot=()=>true;
const serverSnapshot=()=>false;

// A streamed boundary may hydrate after the provider has restored a saved locale.
// Its first render must still match the server's English snapshot.
export function useHydrated(){return useSyncExternalStore(subscribe,clientSnapshot,serverSnapshot);}
export function useUiTranslation(){
 const result=useTranslation();
 const hydrated=useHydrated();
 return {...result,t:hydrated?result.t:result.i18n.getFixedT('en','translation')};
}
