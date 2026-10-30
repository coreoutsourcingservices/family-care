// Render the actual portal components with synthetic API fixtures, without live writes.
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const root=path.resolve(import.meta.dirname,'../..');
const fixture=`
const base={id:'example-user',public_id:'A000001',full_name:'Example Administrator',email:'admin@example.com',phone_number:'+919876543210',account_status:'ACTIVE',approval_status:'APPROVED',email_verified:true};
export const user=()=>({...base,role:window.__role,full_name:window.__role==='SUPERADMIN'?'Example Organization Owner':'Example Administrator'});
const doc={...base,id:'doctor-one',public_id:'D000001',full_name:'Example Doctor',email:'doctor@example.com',role:'DOCTOR',referral_id:'exampleD000001',doctor:{qualification:'MBBS, MD',specialization:'Pediatrics',medical_registration_number:'EXAMPLE-2026-001',registering_council:'Example Medical Council',nmr_id:'EXAMPLE-NMR',address:'Example Street, New Delhi',clinic_address:'Family Practice, New Delhi',years_of_experience:8,verification_status:'APPROVED',images:{}}};
const members=[{id:'profile-one',full_name:'Example Child',module:'child',owner_id:'family-one',date_of_birth:'2020-06-12'},{id:'profile-two',full_name:'Example Adult',module:'adult',owner_id:'family-two',date_of_birth:'1988-02-18'}];
const patient={...base,id:'family-one',public_id:'C000001',full_name:'Example Family',role:'PATIENT',profile_counts:{total:3,members:2,self:1,child:1,adult:1,women:1}};
export async function api(p){
 if(p.endsWith('/me'))return {user:user()};
 if(p.endsWith('/dashboard'))return {counts:[{role:'DOCTOR',approval_status:'APPROVED',count:7},{role:'DOCTOR',approval_status:'PENDING_APPROVAL',count:2},{role:'PATIENT',approval_status:'APPROVED',count:24},{role:'ADMIN',approval_status:'APPROVED',count:3}]};
 if(p.includes('/doctor-requests')||p.includes('/admin-requests'))return {items:[{...doc,approval_status:'PENDING_APPROVAL'},{...doc,id:'doctor-two',public_id:'D000002',full_name:'Another Example Doctor',approval_status:'PENDING_APPROVAL'}],total:2};
 if(p.includes('/vaccination/')){if(p.includes('/vaccines'))return {items:[{id:'vaccine-one',code:'EXAMPLE_VACCINE',name_en:'Example vaccine',name_hi:'',category:'Government',protects_against:'Source-reviewed indication',active:true}],total:1};return {items:[],total:0};}
 if(p.includes('/doctors/')&&p.includes('/profiles'))return {items:members,total:2};
 if(p.includes('/doctors/'))return {user:doc};
 if(p.includes('/doctors?'))return {items:[doc,{...doc,id:'doctor-two',public_id:'D000002',full_name:'Another Example Doctor',approval_status:'PENDING_APPROVAL',account_status:'ACTIVE'}],total:2};
 if(p.includes('/patients?'))return {items:[patient],total:1};
 if(p.includes('/admins?'))return {items:[{...base,role:'ADMIN'}],total:1};
 if(p.includes('/audit-logs'))return {items:[{id:'event-one',action:'doctor_approved',actor_id:'00000000-0000-4000-8000-000000000001',target_id:'00000000-0000-4000-8000-000000000002',created_at:'2026-10-30T09:00:00Z'}],total:1};
 return {items:[],total:0};
}
export const post=(p,d)=>api(p,d);`;
const entry=`import React from 'react';import{createRoot}from'react-dom/client';import Shell from './admin/src/components/shell';import Dashboard from './admin/src/components/dashboard';import Directory from './admin/src/components/directory';import Settings from './admin/src/components/settings';import Vaccination from './admin/src/components/vaccination-manager';import Doctor from './admin/src/components/doctor-details';import Audit from './admin/src/components/audit';import LanguageProvider from './admin/src/components/language-provider';import{user}from 'portal-fixture';
const role=window.__role;const page=window.__page;const content=page==='dashboard'?<Dashboard role={role} user={user()}/>:page==='settings'?<Settings role={role} user={user()}/>:page==='vaccination'?<Vaccination role={role}/>:page==='doctor-detail'?<Doctor role={role} id='D000001'/>:page==='audit-logs'?<Audit/>:<Directory role={role} kind={page}/>;createRoot(document.getElementById('root')).render(<LanguageProvider><Shell role={role} user={user()}>{content}</Shell></LanguageProvider>);`;
const bundle=await build({stdin:{contents:entry,resolveDir:root,loader:'tsx'},jsx:'automatic',bundle:true,write:false,define:{'process.env.NODE_ENV':'"production"'},plugins:[{name:'synthetic-portal',setup(b){
 b.onResolve({filter:/^react(?:-dom)?(?:\/.*)?$/},a=>({path:require.resolve(a.path)}));
 b.onResolve({filter:/^(portal-fixture|@\/lib\/api)$/},()=>({path:'api',namespace:'fixture'}));
 b.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:fixture}));
 b.onResolve({filter:/^next\/(link|navigation)$/},a=>({path:a.path,namespace:'next-fixture'}));
 b.onLoad({filter:/.*/,namespace:'next-fixture'},a=>({loader:'jsx',contents:a.path.endsWith('link')?`import React from 'react';export default function Link({href,children,onClick,...props}){return <a {...props} href={href} onClick={e=>{e.preventDefault();onClick?.(e);}}>{children}</a>}`:`export const usePathname=()=>window.__path;export const useSearchParams=()=>new URLSearchParams();export const useRouter=()=>({replace(){},refresh(){}});`}));
 b.onResolve({filter:/^@\/lib\/i18n$/},()=>({path:'i18n',namespace:'translation-fixture'}));
 b.onLoad({filter:/.*/,namespace:'translation-fixture'},()=>({contents:`export const useHydrated=()=>true;export const useUiTranslation=()=>({t:(key,vars={})=>Object.entries(vars).reduce((value,[name,replacement])=>value.replaceAll('{{'+name+'}}',String(replacement)),vars.defaultValue||key)});`}));
 b.onResolve({filter:/^@\//},a=>{const base=path.join(root,'admin/src',a.path.slice(2));return {path:[base,base+'.tsx',base+'.ts',base+'.json'].find(p=>fs.existsSync(p)&&fs.statSync(p).isFile())};});
}}]});
const browser=await chromium.launch({channel:'chrome',headless:true});
const css=fs.readFileSync(path.join(root,'admin/src/app/globals.css'),'utf8').split('\n').slice(1).join('\n')+'\n'+fs.readFileSync(path.join(root,'admin/src/app/portal.css'),'utf8');
fs.mkdirSync(path.join(root,'test-results/portal'),{recursive:true});
const errors=[];
try{
 for(const role of ['ADMIN','SUPERADMIN']){
  for(const name of ['dashboard','doctors','patients','doctor-detail','vaccination','settings',...(role==='SUPERADMIN'?['admins','audit-logs']:[])]){
   const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(role+'/'+name+': '+e.message));
   await page.setContent('<div id="root"></div>');await page.evaluate(({role,name})=>{window.__role=role;window.__page=name;window.__path=(role==='SUPERADMIN'?'/superadmin':'')+'/'+(name==='doctor-detail'?'doctors/D000001':name);window.fetch=async()=>({ok:true,json:async()=>({languages:[{code:'en',name:'English',translation_status:'available'}],location:{state:''},recommended_language:'en',items:[{name:'Delhi',languages:[{code:'en',name:'English',translation_status:'available'}]}],translation_status:'available',messages:{}})});},{role,name});
   await page.addStyleTag({content:css});await page.addScriptTag({content:bundle.outputFiles[0].text});await page.locator('.page-content h1').waitFor();await page.locator('.language-selector select').first().waitFor();
   await page.getByText('Loading doctor profile...',{exact:true}).waitFor({state:'hidden'});
   if(name==='vaccination'){
    await page.getByRole('button',{name:'Deactivate Example vaccine',exact:true}).waitFor();
    await page.getByRole('button',{name:'Add dose schedule',exact:true}).click();
    await page.getByLabel('Age unit',{exact:true}).selectOption('months');
    await page.getByLabel('Recommended age start',{exact:true}).fill('6');
    await page.getByLabel('Recommended age end',{exact:true}).fill('6');
    assert.equal(await page.getByLabel('Active dose',{exact:true}).isChecked(),true);
    assert.equal(await page.getByLabel('Show in child and connected doctor plan',{exact:true}).isChecked(),true);
   }
   if(['dashboard','doctor-detail'].includes(name))await page.screenshot({path:path.join(root,`test-results/portal/${role.toLowerCase()}-${name}-desktop.png`),fullPage:true});
   for(const width of [1024,390]){
    await page.setViewportSize({width,height:900});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${role}/${name}: overflow at ${width}`);
    if(width===390){const menu=page.getByRole('button',{name:'Open navigation',exact:true});await menu.click();assert.equal(await menu.getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await menu.getAttribute('aria-expanded'),'false');await page.waitForFunction(()=>document.querySelector('.sidebar').getBoundingClientRect().right<=0);}
   }
   if(['dashboard','doctor-detail','vaccination'].includes(name))await page.screenshot({path:path.join(root,`test-results/portal/${role.toLowerCase()}-${name}-mobile.png`),fullPage:true});
   await page.close();console.log('PASS',role,name,'desktop, tablet, mobile and navigation');
  }
 }
 assert.deepEqual(errors,[]);
}finally{await browser.close();}
