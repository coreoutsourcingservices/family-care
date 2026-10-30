'use client';
import {createContext,useContext,useEffect,useState,useRef} from 'react';
import {createInstance} from 'i18next';
import {I18nextProvider} from 'react-i18next';
import {useHydrated,useUiTranslation as useTranslation} from '@/lib/i18n';
import english from '@/locales/en.json';
import {MapPin,Globe,ChevronDown} from 'lucide-react';
type Option={code:string;name:string;native_name?:string;translation_status:string};
type State={name:string;languages:Option[]};
const Languages=createContext({options:[] as Option[],states:[] as State[],state:'',language:'en',error:'',change:(_language:string)=>{},chooseState:(_state:string)=>{}});
export default function LanguageProvider({children}:{children:React.ReactNode}){
 const [i18n]=useState(()=>{const instance=createInstance();void instance.init({lng:'en',fallbackLng:'en',resources:{en:{translation:english}},keySeparator:false,nsSeparator:false,interpolation:{escapeValue:false},initAsync:false});return instance;});
 const [options,setOptions]=useState<Option[]>([{code:'hi',name:'Hindi',translation_status:'available'},{code:'en',name:'English',translation_status:'available'}]);
 const version=useRef(0),stateVersion=useRef(0),manualSelection=useRef(false);
 const [states,setStates]=useState<State[]>([]),[state,setState]=useState(''),[language,setLanguage]=useState('en'),[error,setError]=useState('');
 async function change(code:string,persist=true){
  if(persist)manualSelection.current=true;
  const requestVersion=++version.current;setError('');
  try{
   const response=await fetch(`/api/v1/localization/messages/${encodeURIComponent(code)}`);if(!response.ok)throw new Error();
   const data=await response.json();if(requestVersion!==version.current)return;
   if(data.translation_status!=='available'){setError('Translation unavailable');return;}
   i18n.addResourceBundle(code,'translation',data.messages,true,true);await i18n.changeLanguage(code);if(requestVersion!==version.current)return;
   setLanguage(code);document.documentElement.lang=code;document.documentElement.dir=code==='ur'?'rtl':'ltr';
   if(persist){try{localStorage.setItem('familycare-language',code);}catch{}}
  }catch{if(requestVersion===version.current)setError('Unable to change language. Please try again.');}
 }
 async function chooseState(name:string){
  const requestVersion=++stateVersion.current;
  try{const r=await fetch(`/api/v1/localization?state=${encodeURIComponent(name)}`);if(!r.ok)return;const d=await r.json();if(requestVersion!==stateVersion.current)return;setState(d.location.state||'');setOptions(d.languages);}catch{}
 }
 useEffect(()=>{
  let active=true;let saved:string|null=null;try{saved=localStorage.getItem('familycare-language');}catch{}
  manualSelection.current=!!saved;if(saved)void change(saved,false);
  const initialStateVersion=stateVersion.current;
  void fetch('/api/v1/localization').then(r=>r.json()).then(d=>{if(!active||!d.languages||initialStateVersion!==stateVersion.current)return;setOptions(d.languages);setState(d.location.state||'');if(!manualSelection.current)void change(d.recommended_language,false);}).catch(()=>{});
  void fetch('/api/v1/localization/states').then(r=>r.json()).then(d=>{if(active&&d.items)setStates(d.items);}).catch(()=>{});
  return()=>{active=false;};
 },[]);
 return <I18nextProvider i18n={i18n}><Languages.Provider value={{options,states,state,language,error,change,chooseState}}>{children}</Languages.Provider></I18nextProvider>;
}
export function LanguageSelector(){
 const hydrated=useHydrated();const {t}=useTranslation();const {options,states,state,language,error,change,chooseState}=useContext(Languages);
 const [allOptions,setAllOptions]=useState<Option[]|null>(null),[showAll,setShowAll]=useState(false),[loadingAll,setLoadingAll]=useState(false),[listError,setListError]=useState(false);
 async function otherLanguages(){
  setShowAll(true);setListError(false);if(allOptions)return;setLoadingAll(true);
  try{const r=await fetch('/api/v1/localization/languages');if(!r.ok)throw new Error();const d=await r.json();if(!Array.isArray(d.items))throw new Error();setAllOptions(d.items);}catch{setListError(true);}finally{setLoadingAll(false);}
 }
 const selected=(allOptions||states.flatMap(s=>s.languages)).find(o=>o.code===language)||{code:language,name:language,translation_status:'available'};
 const visible=showAll&&allOptions?allOptions:options;
 const choices=visible.some(x=>x.code===language)?visible:[...visible,selected];
 if(!hydrated)return <div className="language-selector" aria-busy="true"/>;
 return <div className="language-selector"><label className="portal-select-control"><MapPin size={17} aria-hidden="true"/><select aria-label={t('Choose state')} value={state} onChange={e=>chooseState(e.target.value)}><option value="">{t('Choose state')}</option>{states.map(s=><option key={s.name}>{s.name}</option>)}</select><ChevronDown className="portal-select-chevron" size={14} aria-hidden="true"/></label><label className="portal-select-control"><Globe size={17} aria-hidden="true"/><select aria-label={t('Language')} value={language} onChange={e=>e.target.value==='__other__'?void otherLanguages():change(e.target.value)}>{choices.map(o=><option key={o.code} value={o.code} disabled={o.translation_status!=='available'}>{o.native_name||o.name}{o.translation_status!=='available'?` (${t('Translation unavailable')})`:''}</option>)}{!showAll&&<option value="__other__">{t('Other languages')}</option>}</select><ChevronDown className="portal-select-chevron" size={14} aria-hidden="true"/></label>{showAll&&<button type="button" className="text-button" onClick={()=>setShowAll(false)}>{t('Regional languages')}</button>}{loadingAll&&<span role="status">{t('Loading languages')}</span>}{listError&&<button type="button" className="text-button" onClick={otherLanguages}>{t('Try again')}</button>}{error&&<span role="status" className="error-text">{t(error)}</span>}</div>;
}
