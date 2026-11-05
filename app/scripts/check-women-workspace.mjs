import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile,mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const result=JSON.parse(await readFile('app/public/demo/women/ocr-result.json','utf8'));
const profile={id:'de000000-0000-4000-8000-000000000099',profile_type:'member',module:'women',full_name:'Demo Woman (Sample)',date_of_birth:'1996-04-12',gender:'Female',created_at:'2026-11-05',family_access:true};
const doctors=[{id:'demo-gyn',name:'Dr Demo Meera',specialization:'Gynaecology',qualification:'Illustrative demo clinician',experience:12,rating:null,review_count:0,referral_id:'DEMO'},{id:'demo-endo',name:'Dr Demo Asha',specialization:'Endocrinology',qualification:'Illustrative demo clinician',experience:10,rating:null,review_count:0,referral_id:'DEMO'}];
const records=[{id:'demo-cycle',section:'cycle',date:'2026-11-01',title:'DEMO - Cycle entry',flow:'Medium',notes:'Synthetic preview entry'},{id:'demo-meal',section:'nutrition',date:'2026-11-05',title:'DEMO - Meal journal',category:'Meals',notes:'Rice, dal and vegetables - synthetic example'}];
try{
 await mkdir('app/.preview',{recursive:true});
 const page=await browser.newPage({viewport:{width:1366,height:900}});let failSave=false,reportReady=false;let lastDirectory;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/**',async route=>{
 const request=route.request(),url=new URL(request.url()),path=url.pathname;const json=data=>route.fulfill({json:data});
 if(path.endsWith('/patients/me'))return json({user:{id:'demo-owner',role:'PATIENT',full_name:'Demo Family',email:'demo@example.invalid'}});
 if(path==='/api/v1/patients/profiles')return json({items:[profile],total:1});
 if(path==='/api/v1/patients/profiles/'+profile.id)return json({profile});
 if(path.endsWith('/workspace'))return json({profile:{id:profile.id,name:profile.full_name,dob:profile.date_of_birth},owner:true,permissions:{},records,access_expires_at:null});
 if(path.includes('/diary/')&&request.method()==='PUT'){
 if(failSave)return route.fulfill({status:500,json:{error:{message:'Synthetic save failure',code:'save_failed'}}});
 const payload=request.postDataJSON();const record={id:path.split('/').pop(),section:payload.section,...payload.data,version:'1'};records.push(record);return json({record});}
 if(path.endsWith('/doctor-directory')){lastDirectory=url;let items=url.searchParams.get('search')?doctors.filter(d=>(d.name+' '+d.specialization).toLowerCase().includes(url.searchParams.get('search').toLowerCase())):url.searchParams.get('concern')==='PCOS & hormonal'?doctors:[doctors[0]];return json({items,total:items.length});}
 if(path.endsWith('/reports')&&request.method()==='POST'){assert(request.postDataBuffer().includes(Buffer.from('demo-women-lab-report.pdf')));reportReady=true;return json({report:{id:'demo-report',name:'demo-women-lab-report.pdf',created_at:'2026-11-05',category:'Lab tests'}});}
 if(path.endsWith('/reports'))return json({items:reportReady?[{id:'demo-report',name:'demo-women-lab-report.pdf',created_at:'2026-11-05',category:'Lab tests'}]:[],total:reportReady?1:0});
 if(path.endsWith('/report-text/options'))return json({configured:true,translation_enabled:false,languages:[{code:'en',name:'English'}],max_pages:5});
 if(path.endsWith('/text'))return json({analysis:{status:'COMPLETED',options:{source_language:'en',target_language:'en'},result}});
 return json({items:[],total:0,unread_count:0});
 });
 await page.goto('http://127.0.0.1:5173/customer/women/cycle');
 await page.getByRole('button',{name:'Calendar & reminders',exact:true}).click();
 await page.getByLabel('Write a notification').fill('DEMO - Prepare questions');await page.getByRole('button',{name:'Save reminder',exact:true}).click();await expect(page.getByRole('dialog',{name:'Calendar & reminders'})).not.toBeVisible();
 await page.getByRole('button',{name:/Calendar & reminders/}).click();await expect(page.locator('.wh-calendar-reminders')).toContainText('DEMO - Prepare questions');
 failSave=true;await page.getByLabel('Write a notification').fill('Keep unsaved reminder');await page.getByRole('button',{name:'Save reminder',exact:true}).click();await expect(page.getByRole('dialog',{name:'Calendar & reminders'})).toBeVisible();await expect(page.getByLabel('Write a notification')).toHaveValue('Keep unsaved reminder');await page.getByRole('button',{name:'Close calendar'}).click();failSave=false;
 await page.locator('.ch-sidebar a[href="/customer/women/consultation"]').click();await expect(page.locator('.dc-doctors')).toContainText('Dr Demo Meera');await expect(page.locator('.dc-doctors')).not.toContainText('Dr Demo Asha');assert.equal(lastDirectory.searchParams.get('module'),'women');
 await page.getByRole('button',{name:'PCOS & hormonal',exact:true}).click();await expect(page.locator('.dc-doctors')).toContainText('Dr Demo Asha');
 const search=page.getByRole('textbox',{name:'Search doctors',exact:true});await search.fill('Asha');await expect(page.locator('.dc-doctors article')).toHaveCount(1);await expect(page.locator('.dc-doctors')).toContainText('Dr Demo Asha');
 assert.equal(await search.evaluate(e=>getComputedStyle(e).borderTopWidth),'0px');
 await search.fill('unknown');await expect(page.getByText('No approved doctors match this concern or search.',{exact:false})).toBeVisible();await search.fill('');await expect(page.locator('.dc-doctors article')).toHaveCount(2);
 await page.getByRole('textbox',{name:'Search women health'}).fill('nutrition');await expect(page.locator('.wh-ref-search-results')).toBeVisible();await page.keyboard.press('Escape');await expect(page.locator('.wh-ref-search-results')).not.toBeVisible();
 await page.screenshot({path:'app/.preview/women-consultation-demo-1366.png',fullPage:true});
 await page.locator('.ch-sidebar a[href="/customer/women/records"]').click();await page.getByLabel('Upload medical reports').setInputFiles('app/public/demo/women/demo-women-lab-report.pdf');
 await expect(page.getByText('Original extracted text',{exact:true})).toBeVisible();await expect(page.locator('.report-text-results pre').first()).toContainText('Hemoglobin');await expect(page.locator('.report-text-results pre').first()).toContainText('12.4');
 await page.screenshot({path:'app/.preview/women-report-demo-1366.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile overflow');await page.screenshot({path:'app/.preview/women-report-demo-390.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS women reminder save/close and failure retention; concern filtering; search and empty state; search layout/Escape; sample PDF upload and actual OCR result display; mobile overflow.');
}finally{await browser.close();}
