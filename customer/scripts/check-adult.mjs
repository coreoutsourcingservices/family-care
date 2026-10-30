import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({reducedMotion:'reduce'});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const id='11111111-1111-4111-8111-111111111111';
const profile={id,module:'adult',full_name:'Adult Example',date_of_birth:'1985-01-01',profile_type:'member',emergency_contacts:[],created_at:'2026-01-01T00:00:00Z'};
let rows=[];
await page.route('**/api/v1/**',async route=>{const req=route.request(),url=new URL(req.url()),path=url.pathname.replace('/api/v1','');
 if(path==='/patients/me')return route.fulfill({json:{user:{id:'patient-test',full_name:'Family Example',email:'test@example.com',role:'PATIENT'}}});
 if(path==='/patients/profiles')return route.fulfill({json:{items:[profile],total:1}});
 if(path==='/patients/profiles/'+id)return route.fulfill({json:{profile}});
 if(path.endsWith('/reports')||path.endsWith('/imported-records'))return route.fulfill({json:{items:[],total:0}});
 if(path.startsWith('/patients/adults/'+id+'/records')){
  if(req.method()==='GET')return route.fulfill({json:{items:rows}});
  const body=req.postDataJSON();
  if(path.endsWith('/delete'))rows=rows.filter(r=>!path.includes(r.id));
  else {const existing=rows.find(r=>path.endsWith('/'+r.id));if(existing)Object.assign(existing,body);else rows.push({...body,id:crypto.randomUUID()});}
  return route.fulfill({json:{message:'Saved',record:rows.at(-1)}});
 }
 return route.fulfill({status:404,json:{error:{message:'Unexpected mocked path '+path}}});
});
const pages=['dashboard','bp','glucose','lipids','medicine','lifestyle','screening','history','reports','consultation_request','reminder','settings'];
try{
 await mkdir('app/.preview',{recursive:true});
 for(const width of [390,1366,1920]){await page.setViewportSize({width,height:900});for(const part of pages){await page.goto('http://127.0.0.1:5173/customer/adult/'+part);await expect(page.locator('.ah-header')).toBeVisible();await expect(page.locator('.ah-content')).toBeVisible();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,part+' overflow '+width);}await page.goto('http://127.0.0.1:5173/customer/adult/dashboard');await expect(page.getByRole('heading',{name:'Blood pressure trend'})).toBeVisible();await page.screenshot({path:'app/.preview/adult-empty-'+width+'.png',fullPage:true});console.log('PASS all 12 adult pages at '+width+'px');}
 await page.goto('http://127.0.0.1:5173/customer/adult/bp');
 await page.getByRole('button',{name:'Add record',exact:true}).click();
 await page.getByLabel('Title *',{exact:true}).fill('Morning BP');
 await page.getByLabel('Systolic (mmHg) *',{exact:true}).fill('120');
 await page.getByLabel('Diastolic (mmHg) *',{exact:true}).fill('80');
 await page.getByRole('button',{name:'Save record',exact:true}).click();
 await expect(page.locator('tbody tr')).toHaveCount(1);
 await page.getByRole('button',{name:'Edit Morning BP'}).click();
 await page.getByLabel('Systolic (mmHg) *',{exact:true}).fill('125');
 await page.getByRole('button',{name:'Save record',exact:true}).click();
 await expect(page.locator('tbody')).toContainText('125');
 for(const [kind,label,value] of [['glucose','Blood glucose (mg/dL) *','95'],['lipids','Total cholesterol (mg/dL) *','180']]){await page.goto('http://127.0.0.1:5173/customer/adult/'+kind);await page.getByRole('button',{name:'Add record',exact:true}).click();await page.getByLabel('Title *',{exact:true}).fill(kind+' reading');await page.getByLabel(label,{exact:true}).fill(value);await page.getByRole('button',{name:'Save record',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(1);}
 await page.goto('http://127.0.0.1:5173/customer/adult/reminder');await page.getByRole('button',{name:'Add record',exact:true}).click();await page.getByLabel('Title *',{exact:true}).fill('Take prescribed medicine');await page.getByRole('button',{name:'Save record',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(1);
 await page.goto('http://127.0.0.1:5173/customer/adult/dashboard');await expect(page.locator('canvas')).toHaveCount(3);await expect(page.getByRole('link',{name:'1 due reminders'})).toBeVisible();await page.screenshot({path:'app/.preview/adult-populated-1920.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Open navigation'}).click();await expect(page.getByRole('navigation',{name:'',exact:true})).toBeVisible();await page.getByRole('button',{name:'Close navigation',exact:true}).click();
 await page.goto('http://127.0.0.1:5173/customer/adult/bp');page.once('dialog',dialog=>dialog.accept());await page.getByRole('button',{name:'Delete Morning BP'}).click();await expect(page.locator('tbody tr')).toHaveCount(0);assert.equal(rows.some(r=>r.kind==='bp'),false);
 assert.deepEqual(errors,[]);console.log('PASS real form interactions, save/edit/delete, persisted reload, three Chart.js charts, cross-page reminder badge and mobile menu. APIs mocked; no real health records changed.');
}finally{await browser.close();}
