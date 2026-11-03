// Actual React components with synthetic data; never mutates live patient records.
import {build} from 'esbuild';
import {chromium,expect} from '@playwright/test';
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const require=createRequire(import.meta.url),root=process.cwd();
const entry=`import React from 'react';import {createRoot} from 'react-dom/client';import {MemoryRouter,Routes,Route} from 'react-router-dom';
import Vaccination from './customer/src/modules/child/Vaccination';
import AdultRecords from './customer/src/modules/adult/AdultRecords';
import {WomenDiary} from './customer/src/modules/women/WomenPages';
import Appointments from './doctor/src/pages/Appointments';
import Prescriptions from './doctor/src/pages/Prescriptions';
import Guard from './app/src/components/MemberRouteGuard';
const profile={id:'profile',name:'Synthetic Patient',dob:'2018-01-01',module:'child',reports:[],contacts:[],referral:{type:'self',code:''},profileType:'member'};
const entries=[{id:'linked',kind:'vaccination',title:'Linked saved dose',date:'2026-01-01',status:'Completed',schedule_id:'dose1',source_role:'DOCTOR'},{id:'external',kind:'vaccination',title:'External vaccine',date:'2026-02-01',status:'Completed',source_role:'DOCTOR'}];
const store={records:[],add:async record=>{window.saved=record;return true},remove:async()=>true};
const kind=window.screenKind;
const component=kind==='vaccination'?<Vaccination entries={entries} profileId="profile" profile={profile} onAdd={async()=>true}/>:kind==='adult'?<AdultRecords kind="bp" profile={{...profile,module:'adult',dob:'1990-01-01'}} records={[]} ready onRefresh={async()=>{}}/>:kind==='women'?<WomenDiary section="screening" store={store}/>:kind==='appointments'?<Appointments/>:kind==='prescriptions'?<Prescriptions/>:<Routes><Route path="/customer/dashboard" element={<Guard><p>PROTECTED RECORDS</p></Guard>}/><Route path="/customer/login" element={<p>Sign in page</p>}/></Routes>;
createRoot(document.getElementById('root')).render(<MemoryRouter initialEntries={['/customer/dashboard']}><main className={kind==='adult'?'ah-app':kind==='women'?'ch-app wh-app':kind==='vaccination'?'ch-app':'doctor-home'} style={{display:'block',padding:16}}>{component}</main></MemoryRouter>);`;
const apiMock=`export async function careApi(path,body,retry,method){window.calls.push({path,body,method});
 if(path.includes('/vaccinations/history'))return {items:[],total:0};
 if(path.includes('/vaccinations?'))return {items:path.includes('UIP')?[{id:'dose1',vaccine:{name_en:'Synthetic vaccine'},dose_name:'Dose 1',age_label:'Birth',recommended_date:'2018-01-01',age_group:'0-1',status:'COMPLETED',publication_status:'PUBLISHED'}]:[]};
 if(path.startsWith('/doctors/care-profiles?'))return {items:[{id:'profile',full_name:'Synthetic Patient',module:'child'}],total:1};
 if(path==='/women/shared'||path==='/adult-access/shared')return {items:[]};
 if(path==='/doctors/consultation-visits')return {items:[{id:'visit',patient_name:'Synthetic Patient',concern:'Synthetic visit',requested_at:'2030-01-01T10:00:00Z',confirmed_at:null,status:'REQUESTED',duration_minutes:30,version:1}]};
 if(path.endsWith('/status'))return {consultation:{}};
 if(path==='/doctors/appointment-slots')return {items:[]};
 if(path.includes('/prescriptions'))return body?{prescription:{id:'rx'}}:{items:[]};
 return {items:[],total:0};}`;
const authMock=`export class ApiError extends Error{constructor(message,code,status){super(message);this.code=code;this.status=status}};export async function authApi(){throw new ApiError('Synthetic session failure','invalid_token',window.authStatus||0)};export function publicPortal(){return 'patient'};export async function refreshSession(){return {}};`;
const bundle=await build({stdin:{contents:entry,resolveDir:root,loader:'tsx'},jsx:'automatic',bundle:true,write:false,define:{'process.env.NODE_ENV':'"production"','import.meta.env.VITE_API_BASE_URL':'""'},plugins:[{name:'synthetic',setup(b){
 b.onResolve({filter:/^react(?:-dom)?(?:\/.*)?$|^react-router-dom$/},a=>({path:require.resolve(a.path)}));
 b.onResolve({filter:/\/careApi$/},()=>({path:'api',namespace:'fixture'}));b.onResolve({filter:/\/authApi$/},()=>({path:'auth',namespace:'fixture'}));
 b.onResolve({filter:/\/DoctorWorkspaceLayout$/},()=>({path:'layout',namespace:'fixture'}));
 b.onLoad({filter:/.*/,namespace:'fixture'},a=>({contents:a.path==='api'?apiMock:a.path==='auth'?authMock:`import React from 'react';export default function Layout({children}){return <div className="doctor-workspace-content">{children}</div>}`,loader:'tsx'}));
 b.onResolve({filter:/\.css$/},()=>({path:'css',namespace:'empty'}));b.onLoad({filter:/.*/,namespace:'empty'},()=>({contents:''}));
}}]});
const css=['app/src/styles.css','app/src/pages/customer-dashboard.css','doctor/src/pages/doctor-home.css','customer/src/modules/child/child-care-pages.css','customer/src/modules/adult/adult.css','app/src/audit-responsive.css'].map(file=>fs.readFileSync(path.join(root,file),'utf8')).join('\n');
fs.mkdirSync('.preview',{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 for(const width of [360,390,768,1366,1920,2560]){
  const page=await browser.newPage({viewport:{width,height:900}});
  for(const kind of ['vaccination','adult','women','appointments','prescriptions']){
   await page.setContent('<div id="root"></div>');await page.evaluate(k=>{window.screenKind=k;window.calls=[]},kind);await page.addStyleTag({content:css});await page.addScriptTag({content:bundle.outputFiles[0].text});
   if(kind==='vaccination'){
    await expect(page.getByRole('button',{name:'Completed',exact:true})).toBeVisible();await expect(page.getByText('Synthetic vaccine / Dose 1',{exact:true})).toHaveCount(1);await expect(page.getByText('Linked saved dose',{exact:true})).toHaveCount(0);await expect(page.getByRole('checkbox')).toHaveCount(0);
    await page.getByRole('button',{name:'Completed',exact:true}).click();
   }else if(kind==='adult'){
    await page.getByRole('button',{name:'Add record',exact:true}).click();await expect(page.getByRole('combobox',{name:'Arm',exact:true})).toBeVisible();await expect(page.getByRole('combobox',{name:'Position',exact:true})).toBeVisible();
   }else if(kind==='women'){
    await page.getByRole('button',{name:'Add record',exact:true}).click();await expect(page.getByRole('option',{name:'Result received',exact:true})).toHaveCount(1);await page.getByRole('button',{name:'Close form'}).click();
   }else if(kind==='appointments'){
    await page.getByRole('button',{name:'Confirm time',exact:true}).click();await expect(page.getByLabel('Confirmed start')).toBeVisible();await page.getByRole('button',{name:'Confirm appointment',exact:true}).click();await expect.poll(()=>page.evaluate(()=>window.calls.some(c=>c.path.endsWith('/status')&&c.body.confirmed_at&&c.body.version===1))).toBeTruthy();
   }else{
    await page.getByRole('combobox',{name:'Patient',exact:true}).selectOption('profile');await page.getByRole('button',{name:'New prescription',exact:true}).click();await expect(page.getByLabel('strength',{exact:true})).toBeVisible();
   }
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow){console.log(await page.evaluate(()=>[...document.querySelectorAll('*')].filter(n=>n.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(n=>({tag:n.tagName,cls:n.className,width:n.getBoundingClientRect().width,right:n.getBoundingClientRect().right}))));await page.screenshot({path:'.preview/audit-overflow.png',fullPage:true});}expect(overflow,kind+' overflows at '+width).toBe(false);
   if([390,1920].includes(width))await page.screenshot({path:'.preview/audit-'+kind+'-'+width+'.png',fullPage:true});
  }
  await page.close();
 }
 const page=await browser.newPage();for(const status of [0,401]){await page.setContent('<div id="root"></div>');await page.evaluate(s=>{window.screenKind='guard';window.authStatus=s;window.calls=[]},status);await page.addScriptTag({content:bundle.outputFiles[0].text});await expect(page.getByText('PROTECTED RECORDS',{exact:true})).toHaveCount(0);await expect(status?page.getByText('Sign in page',{exact:true}):page.getByRole('button',{name:'Retry session check'})).toBeVisible();}await page.close();
 console.log('PASS: five real screens at 360/390/768/1366/1920/2560px; vaccination reconciliation, structured forms, appointment confirmation, prescription draft UI and fail-closed session guard');
}finally{await browser.close()}
