// Actual doctor component, synthetic records; no local database mutations.
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url),root=path.resolve(import.meta.dirname,'../..');
const fixture=`
const doc={id:'doctor-one',public_id:'D000001',full_name:'Dr Example Sharma',email:'doctor@example.com',phone_number:'+919876543210',approval_status:'APPROVED',account_status:'ACTIVE',referral_id:'exampleD000001',doctor:{qualification:'MBBS, MD (Pediatrics)',specialization:'Pediatrics',years_of_experience:9,medical_registration_number:'TEST-12345',registering_council:'Example Council',clinic_address:'Example Clinic, Delhi',verification_status:'VERIFIED',images:{}}};
const family={id:'family-one',public_id:'C000001',full_name:'Example Family',connected_profiles:2};
const members=[{id:'member-one',full_name:'Example Child',module:'child',date_of_birth:'2018-02-14',gender:'Female',profile_type:'member',updated_at:'2026-11-03T09:00:00Z',owner_id:'family-one',family_name:'Example Family',family_public_id:'C000001'},{id:'member-two',full_name:'Example Adult',module:'adult',date_of_birth:'1990-05-01',profile_type:'self',updated_at:'2026-11-02T09:00:00Z',owner_id:'family-one',family_name:'Example Family',family_public_id:'C000001'}];
export async function api(p){window.__calls.push(p);if(window.__fail)throw Error('Network unavailable');const u=new URL(p,'http://test/'),q=u.searchParams;if(!p.includes('/families')&&!p.includes('/profiles'))return {user:doc,dashboard:{connected_profiles:2,families:1,child:1,adult:1,women:0}};
if(u.pathname.endsWith('/families')){const items=!q.get('search')||family.full_name.toLowerCase().includes(q.get('search').toLowerCase())?[family]:[];return {items,total:items.length};}
let items=members.filter(m=>(!q.get('module')||m.module===q.get('module'))&&(!q.get('search')||m.full_name.toLowerCase().includes(q.get('search').toLowerCase())));if(p.includes('/families/')){if(p.includes('/profiles/'))items=items.filter(m=>u.pathname.endsWith(m.id));return {family,items,total:items.length};}return {items,total:items.length};}
`;
const entry=`import React from 'react';import{createRoot}from'react-dom/client';import Doctor from './admin/src/components/doctor-details';const root=createRoot(document.getElementById('root'));window.__render=(familyId,memberId)=>root.render(<div><aside className="sidebar">Existing sidebar</aside><main className="workspace-main"><div className="page-content"><Doctor key={String(familyId)+String(memberId)} role={window.__role} id="doctor-one" familyId={familyId} memberId={memberId}/></div></main></div>);window.__render();`;
const bundle=await build({stdin:{contents:entry,resolveDir:root,loader:'tsx'},jsx:'automatic',bundle:true,write:false,define:{'process.env.NODE_ENV':'"production"'},plugins:[{name:'network-fixture',setup(b){
 b.onResolve({filter:/^react(?:-dom)?(?:\/.*)?$/},a=>({path:require.resolve(a.path)}));
 b.onResolve({filter:/^@\/lib\/api$/},()=>({path:'api',namespace:'fixture'}));b.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:fixture}));
 b.onResolve({filter:/^next\/link$/},()=>({path:'link',namespace:'next'}));b.onLoad({filter:/.*/,namespace:'next'},()=>({loader:'jsx',contents:`import React from 'react';export default function Link({href,children,...props}){return <a {...props} href={href} onClick={e=>{e.preventDefault();const parts=href.split('/'),f=parts.indexOf('families'),p=parts.indexOf('profiles');window.__render(f>=0?parts[f+1]:undefined,p>=0?parts[p+1]:undefined);}}>{children}</a>}`}));
 b.onResolve({filter:/^@\//},a=>({path:path.join(root,'admin/src',a.path.slice(2)+'.ts')}));
}}]});
const css=['globals.css','portal.css','superadmin.css','doctor-network.css'].map(p=>fs.readFileSync(path.join(root,'admin/src/app',p),'utf8').replace(/^@import.*$/gm,'')).join('\n')+fs.readFileSync(path.join(root,'app/src/audit-responsive.css'),'utf8');
const browser=await chromium.launch({channel:'chrome',headless:true}),errors=[];
fs.mkdirSync(path.join(root,'.preview/doctor-network'),{recursive:true});
try{for(const role of ['ADMIN','SUPERADMIN'])for(const width of [360,390,768,1366,1920,2560]){
 const page=await browser.newPage({viewport:{width,height:1050}});page.on('pageerror',e=>errors.push(e.message));await page.setContent('<div id="root"></div>');await page.evaluate(role=>{window.__role=role;window.__calls=[];},role);await page.addStyleTag({content:css});await page.addScriptTag({content:bundle.outputFiles[0].text});
 const ready=()=>page.getByRole('heading',{name:'Dr Example Sharma',exact:true}).first().waitFor();await ready();
 for(const tab of ['Dashboard','Family','Connected Members','Professional Info','Verification','Settings']){
  await page.getByRole('button',{name:tab,exact:true}).click();await ready();await page.waitForFunction(()=>!document.querySelector('[role="status"]'));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${role}/${width}/${tab} overflow`);
  if((width===390||width===1920)&&['Dashboard','Family'].includes(tab))await page.screenshot({path:path.join(root,'.preview/doctor-network',`${role}-${width}-${tab}.png`),fullPage:true});
 }
 await page.getByRole('button',{name:'Connected Members',exact:true}).click();await ready();await page.getByLabel('Care type',{exact:true}).selectOption('child');await page.waitForFunction(()=>document.querySelectorAll('tbody tr').length===1);assert.equal(await page.getByText('Example Adult',{exact:true}).count(),0);
 await page.getByRole('button',{name:'Reset filters',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('tbody tr').length===2);
 await page.getByLabel('Search connected members').fill('no match');await page.getByRole('heading',{name:'No connected profiles found'}).waitFor();await page.getByRole('button',{name:'Reset filters',exact:true}).click();await page.getByRole('link',{name:/View profile/}).first().waitFor();
 assert((await page.getByRole('link',{name:/View profile/}).first().getAttribute('href')).startsWith(role==='ADMIN'?'/doctors/':'/superadmin/doctors/'));
 await page.getByRole('link',{name:/View profile/}).first().click();await page.getByRole('heading',{name:'Member details',exact:true}).waitFor();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.getByRole('link',{name:'Back to family'}).click();await page.getByRole('heading',{name:'Connected family members'}).waitFor();assert.equal(await page.locator('tbody tr').count(),2);
 await page.evaluate(()=>{window.__fail=true;});await page.getByRole('button',{name:'Refresh',exact:true}).click();await page.getByRole('alert').waitFor();assert.equal(await page.locator('tbody tr').count(),0);await page.evaluate(()=>{window.__fail=false;});await page.getByRole('button',{name:'Try again'}).click();await page.getByRole('heading',{name:'Connected family members'}).waitFor();
 await page.close();console.log(`${role} ${width}: tabs, filter, search, links, scoped drilldown, error/retry passed`);
}assert.deepEqual(errors,[]);}finally{await browser.close();}
