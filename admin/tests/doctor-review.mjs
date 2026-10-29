// Isolated UI harness uses the real Directory/DoctorReview components with fake API data.
// No live admin credentials, doctor records or external provider calls are used.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const harness=path.join(root,'.test-data/doctor-review-ui');
await mkdir(harness,{recursive:true});
await writeFile(path.join(harness,'index.html'),'<html><body><div id="root"></div><script type="module" src="/main.tsx"></script></body></html>');
await writeFile(path.join(harness,'main.tsx'),`import React from 'react';import{createRoot}from'react-dom/client';import Directory from '../../admin/src/components/directory';import '../../admin/src/app/globals.css';createRoot(document.getElementById('root')!).render(<main style={{padding:24,maxWidth:1400,margin:'auto'}}><Directory role="ADMIN" kind="doctors"/></main>);`);
await writeFile(path.join(harness,'i18n.ts'),`export const useUiTranslation=()=>({t:(s:string,o?:Record<string,string>)=>o?Object.entries(o).reduce((v,[k,x])=>v.replace('{{'+k+'}}',x),s):s});`);
await writeFile(path.join(harness,'navigation.ts'),`export const useSearchParams=()=>new URLSearchParams(location.search);`);
await writeFile(path.join(harness,'link.tsx'),`import React from 'react';export default function Link(p:any){return <a {...p}/>;}`);
const alias=[
 {find:'@/lib/i18n',replacement:path.join(harness,'i18n.ts')},
 {find:'next/navigation',replacement:path.join(harness,'navigation.ts')},
 {find:'next/link',replacement:path.join(harness,'link.tsx')},
 {find:'@',replacement:path.join(root,'admin/src')},
 {find:'react',replacement:path.join(root,'admin/node_modules/react')},
 {find:'react-dom',replacement:path.join(root,'admin/node_modules/react-dom')},
];
await writeFile(path.join(harness,'vite.config.mjs'),`export default {root:${JSON.stringify(harness)},resolve:{alias:${JSON.stringify(alias)},dedupe:['react','react-dom']},esbuild:{jsx:'automatic'},server:{host:'127.0.0.1',port:5199,strictPort:true,fs:{allow:[${JSON.stringify(root)}]}}};`);
const server=spawn(process.execPath,[path.join(root,'node_modules/vite/bin/vite.js'),'--config',path.join(harness,'vite.config.mjs')],{cwd:root,windowsHide:true,stdio:'pipe'});
let logs='';server.stderr.on('data',data=>{logs+=data});
const browser=await chromium.launch({channel:'msedge'});
const person={id:'fixture-id',public_id:'D_FIXTURE',full_name:'Dr Example Kumar',email:'fixture@example.com',phone_number:'+919876543210',role:'DOCTOR',approval_status:'PENDING_APPROVAL',doctor_status:'pending',account_status:'ACTIVE',email_verified:true,doctor:{qualification:'MBBS',medical_registration_number:'REG-12345',registering_council:'Delhi Medical Council',specialization:'General Medicine',nmr_id:null,address:'12 Example Street, Delhi 110001',clinic_address:'Example Clinic, Delhi 110002',years_of_experience:5,verification_status:'PENDING'}};
const report={checked_at:new Date().toISOString(),registration:{provider:'AskMyDoc (third party)',status:'match',message:'Name, registration and council match.',comparisons:{registration:true,name:true,council:true},records:[{name:'Example Kumar',registration:'REG-12345',council:'Delhi'}]},address:{provider:'India Postal PIN API',status:'area_match',pincode:'110001',message:'Postal area only.'},clinic_postal:{status:'area_match',pincode:'110002',message:'Postal area only.'},clinic:{provider:'OpenStreetMap Nominatim',status:'unavailable',message:'Location service unavailable; check HFR manually.'},requires_admin_review:true,auto_approved:false};
let checks=0,approvals=0,rejections=0;
try{
 for(let attempt=0;attempt<60;attempt++){try{if((await fetch('http://127.0.0.1:5199')).ok)break;}catch{}await new Promise(r=>setTimeout(r,500));}
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(60000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://fonts.googleapis.com/**',route=>route.fulfill({contentType:'text/css',body:''}));
 await page.route('**/api/v1/**',async route=>{const url=new URL(route.request().url());let json;
  if(url.pathname.endsWith('/check')){checks++;json={verification_check:report,doctor_status:'pending',cached:false};}
  else if(url.pathname.endsWith('/approve')){approvals++;person.approval_status='APPROVED';person.doctor_status='verified';json={user:person};}
  else if(url.pathname.endsWith('/reject')){assert.ok(route.request().postDataJSON().reason);rejections++;person.approval_status='REJECTED';person.doctor_status='rejected';json={user:person};}
  else json={items:[person],total:1,page:1,per_page:15};
  await route.fulfill({json});
 });
 await page.goto('http://127.0.0.1:5199',{waitUntil:'domcontentloaded',timeout:60000});
 await page.getByRole('button',{name:'Check Doctor',exact:true}).click();
 const checkDialog=page.getByRole('dialog',{name:'Check Doctor',exact:true});
 await checkDialog.getByText('Name, registration and council match.',{exact:true}).waitFor();
 assert.equal(checks,1);assert.equal(approvals,0);assert.equal(rejections,0);
 await checkDialog.getByText(person.doctor.clinic_address,{exact:true}).waitFor();
 assert.equal(await checkDialog.getByRole('link',{name:'ABDM facility registry'}).count(),1);
 await page.screenshot({path:path.join(root,'.test-data/doctor-review-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:path.join(root,'.test-data/doctor-review-mobile.png'),fullPage:true});
 await checkDialog.getByRole('button',{name:'Approve',exact:true}).click();
 const confirm=page.getByRole('dialog');await confirm.getByRole('button',{name:'Confirm approve',exact:true}).click();
 await page.locator('tbody .badge').filter({hasText:'verified'}).waitFor();assert.equal(approvals,1);
 person.approval_status='PENDING_APPROVAL';person.doctor_status='pending';await page.reload();
 await page.getByRole('button',{name:'Reject',exact:true}).click();
 await page.getByLabel('Reason for rejection').fill('Please correct the clinic details.');
 await page.getByRole('button',{name:'Confirm reject',exact:true}).click();
 await page.locator('tbody .badge').filter({hasText:'rejected'}).waitFor();assert.equal(rejections,1);
 assert.deepEqual(errors,[]);console.log('PASS Check Doctor evidence, full profile, official links, explicit approval/rejection, three statuses and mobile layout.');
}catch(error){console.error(logs);throw error;}finally{await browser.close();server.kill();}
