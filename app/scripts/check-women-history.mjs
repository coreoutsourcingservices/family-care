import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const records=JSON.parse(await readFile('app/public/demo/women/history-entries.json','utf8'));
const browser=await chromium.launch({channel:'chrome',headless:true});
const profile={id:'de000000-0000-4000-8000-000000000099',profile_type:'member',module:'women',full_name:'sfuri - DEMO preview',date_of_birth:'1996-04-12',gender:'Female',created_at:'2025-01-01',family_access:true};
const reports=['Lab tests','Doctor report','Prescriptions','Scans','Vaccination','Others'].map((category,index)=>({id:'demo-report-'+index,name:'DEMO '+category+'.pdf',category,created_at:'2026-06-01',size_bytes:80000}));
const planner=Array.from({length:12},(_,i)=>({id:'demo-note-'+i,kind:i%2?'task':'note',title:'DEMO - Historical '+(i%2?'task':'note')+' '+i,body:'Synthetic previous entry for preview.',completed:i%3===0,due_at:i%2?'2026-11-12T10:00:00Z':null,version:1}));
const errors=[];
try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const path=new URL(route.request().url()).pathname;const json=data=>route.fulfill({json:data});
 if(path.endsWith('/patients/me'))return json({user:{id:'demo-owner',role:'PATIENT',full_name:'Demo account',email:'demo@example.invalid'}});
 if(path==='/api/v1/patients/profiles')return json({items:[profile],total:1});
 if(path==='/api/v1/patients/profiles/'+profile.id)return json({profile});
 if(path.endsWith('/workspace'))return json({profile:{id:profile.id,name:profile.full_name,dob:profile.date_of_birth},owner:true,permissions:{},records});
 if(path.endsWith('/reports'))return json({items:reports,total:reports.length});
 if(path.endsWith('/planner'))return json({items:planner});
 if(path.endsWith('/sharing'))return json({tabs:{health:'My health',cycle:'Period & cycle'},recipients:[],grants:[]});
 if(path.endsWith('/pregnancy-care'))return json({settings:null,guide:null});
 return json({items:[],total:0,unread_count:0});});
 for(const section of ['dashboard','health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening','records','consultation','settings','planner','sharing']){
  await page.goto('http://127.0.0.1:5173/customer/women/'+section);await expect(page.locator('.ch-sidebar')).toBeVisible();await expect(page.locator('.ch-content')).toBeVisible();
  if(['health','cycle','pcos','pregnancy','fertility','symptoms','nutrition','screening'].includes(section))await expect(page.locator('.wh-record').first()).toBeVisible();
  if(section==='consultation'){await page.getByRole('button',{name:'My consultations',exact:true}).click();await expect(page.locator('.dc-columns>div .dc-saved-history .dc-visit')).toHaveCount(6);}
  if(section==='records')await expect(page.locator('.women-report-upload .wh-task')).toHaveCount(6);
  if(section==='planner')await expect(page.locator('.planner-grid article')).toHaveCount(12);
  if(['dashboard','pregnancy','consultation','planner'].includes(section))await page.screenshot({path:'app/.preview/women-history-'+section+'-1366.png',fullPage:true});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Desktop overflow '+section);
  console.log('PASS sidebar '+section);
 }
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:5173/customer/women/consultation');await page.getByRole('button',{name:'My consultations',exact:true}).click();await expect(page.locator('.dc-columns>div .dc-saved-history .dc-visit')).toHaveCount(6);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'app/.preview/women-history-consultation-390.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS full history desktop/mobile and no runtime errors');
}finally{await browser.close();}
