import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile,mkdir} from 'node:fs/promises';
const records=JSON.parse(await readFile('app/public/demo/adult/history-entries.json','utf8'));
const profile={id:'de000000-0000-4000-8000-000000000099',profile_type:'self',module:'adult',full_name:'Priyanshu - DEMO preview',date_of_birth:'1990-01-01',gender:'Male',created_at:'2025-01-01',family_access:true};
const reports=['Lab tests','Doctor report','Prescriptions','Scans','Vaccination','Others'].map((category,i)=>({id:'demo-report-'+i,name:'DEMO Adult '+category+'.pdf',category,created_at:'2026-06-01',size_bytes:80000}));
const planner=Array.from({length:12},(_,i)=>({id:'demo-note-'+i,kind:i%2?'task':'note',title:'DEMO - Adult historical entry '+i,body:'Synthetic previous entry for preview.',completed:i%3===0,due_at:i%2?'2026-11-12T10:00:00Z':null,version:1}));
const ocr=JSON.parse(await readFile('app/public/demo/adult/ocr-result.json','utf8'));
const calls={session:0,profiles:0,details:0,records:0};
const browser=await chromium.launch({channel:'chrome',headless:true});const errors=[];
try{
 await mkdir('app/.preview',{recursive:true});const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',route=>{const path=new URL(route.request().url()).pathname;const json=data=>route.fulfill({json:data});
 if(path.endsWith('/patients/me')){calls.session++;return json({user:{id:'demo-owner',role:'PATIENT',full_name:'Demo account',email:'demo@example.invalid'}});}
 if(path==='/api/v1/patients/profiles'){calls.profiles++;return json({items:[profile],total:1});}
 if(path==='/api/v1/patients/profiles/'+profile.id){calls.details++;return json({profile});}
 if(path.endsWith('/records')){if(path.includes('/adults/'))calls.records++;return json({items:path.includes('/adults/')?records:[],total:path.includes('/adults/')?records.length:0});}
 if(path.endsWith('/reports'))return json({items:reports,total:reports.length});
 if(path.endsWith('/report-text/options'))return json({configured:true,translation_enabled:false,languages:[{code:'en',name:'English'}],max_pages:5});
 if(path.endsWith('/text'))return json({analysis:{status:'COMPLETED',options:{source_language:'en',target_language:'en'},result:ocr}});
 if(path.endsWith('/planner'))return json({items:planner});
 if(path.endsWith('/sharing'))return json({tabs:{bp:'Blood pressure',history:'Medical history'},recipients:[],grants:[]});
 return json({items:[],total:0,unread_count:0});});
 await page.goto('http://127.0.0.1:5173/customer/adult/dashboard?profile='+profile.id);await expect(page.locator('.ah-sidebar')).toBeVisible();await expect(page.locator('.ah-charts canvas').first()).toBeVisible();
 const original=await page.locator('.ah-sidebar').elementHandle();const snapshot={...calls};
 for(const target of ['bp','glucose','lipids','medicine','lifestyle','screening','history','reminder','bp']){
  await page.locator('.ah-sidebar a[href="/customer/adult/'+target+'"]').click();await expect(page.locator('.ah-section-chart canvas')).toBeVisible();assert.equal(await page.locator('.ah-loading').count(),0);assert(await original.evaluate(node=>node===document.querySelector('.ah-sidebar')),'Workspace remounted');
 }
 assert.deepEqual(calls,snapshot,'Internal navigation fetched the session/profile/records again');console.log('PASS retained Adult workspace and no repeated API initialization');
 for(const section of ['dashboard','bp','glucose','lipids','medicine','lifestyle','screening','history','reports','consultation_request','reminder','settings','sharing','planner']){
  await page.goto('http://127.0.0.1:5173/customer/adult/'+section);await expect(page.locator('.ah-sidebar')).toBeVisible();
  if(['bp','glucose','lipids','medicine','lifestyle','screening','history','reminder'].includes(section))await expect(page.locator('.ah-table-wrap tbody tr')).toHaveCount(records.filter(r=>r.kind===section).length);
  if(section==='reports'){await expect(page.locator('.ah-report')).toHaveCount(6);await page.locator('.ah-report').first().getByRole('button',{name:'Read report / Extract text'}).click();await expect(page.locator('.report-text-results pre').first()).toContainText('182');await expect(page.locator('.report-text-results pre').first()).toContainText('94');}
  if(section==='consultation_request'){await page.getByRole('button',{name:'My consultations',exact:true}).click();await expect(page.locator('.dc-columns>div .dc-saved-history .dc-visit')).toHaveCount(6);}
  if(section==='planner')await expect(page.locator('.planner-grid article')).toHaveCount(12);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Desktop overflow '+section);
  if(['dashboard','bp','consultation_request','reports'].includes(section))await page.screenshot({path:'app/.preview/adult-history-'+section+'-1366.png',fullPage:true});
  console.log('PASS Adult sidebar '+section);
 }
 await page.setViewportSize({width:390,height:844});
 for(const section of ['dashboard','bp','reports','consultation_request','planner']){
  await page.goto('http://127.0.0.1:5173/customer/adult/'+section);await expect(page.locator('.ah-app')).toBeVisible();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile overflow '+section);
  if(section==='bp')await page.screenshot({path:'app/.preview/adult-history-bp-390.png',fullPage:true});
 }
 assert.deepEqual(errors,[]);console.log('PASS Adult historical data, all sidebar pages, mobile overflow and runtime');
}finally{await browser.close();}
